"""
Automata for executing rclone commands
"""

import json
import subprocess

from typing import List

from src.shared.constants.Job import Job #pylint: disable=import-error
from src.shared.exceptions.errors.RcloneError import RcloneUploadError, RcloneDownloadError, RcloneDownloadNotFoundError #pylint: disable=import-error
from src.shared.factory.utils.BinUtils import BinUtils #pylint: disable=import-error
from src.shared.factory.utils.DockerUtils import DockerUtils #pylint: disable=import-error
from src.shared.factory.utils.LoggingUtils import LoggingUtils #pylint: disable=import-error
from src.shared.factory.utils.PathUtils import PathUtils #pylint: disable=import-error

class Rclone:

    @staticmethod
    def upload(job: Job, destinations: List[str], upload_file: str, flags: str) -> bool:
        """
        Upload the completed new hardsub file into the rclone destinations
        Returns a boolean based on success

        job: Job to do! This is the job of the HARDSUB file
        destinations: list of rlcone destinations (e.g., EncoderConf.uploading_destinations)
        upload_file: Path to the file to be uploaded
        flags: rclone flag

        This method will upload the file and include its show name:
        e.g., 'temp.mp4' --> destination/show/episode.mp4
        """
        error_occured = False
        for dest in destinations:
            LoggingUtils.debug("Uploading to {}".format(dest))
            rclone_dest = PathUtils.clean_directory_path(dest) + PathUtils.clean_directory_path(job.show) + job.episode
            command = [BinUtils.rclone]
            # If running in Docker, we need to load the user's rclone.conf in the conf folder
            if DockerUtils.docker:
                LoggingUtils.debug("Docker mode detected, referencing rclone config in the conf folder", color=LoggingUtils.YELLOW)
                command.extend(["--config={}".format(DockerUtils.conf + "rclone.conf")])
            else:
                LoggingUtils.debug("Docker mode not detected, using system rclone config", color=LoggingUtils.YELLOW)
            command.extend(["copyto", upload_file, rclone_dest])
            command.extend(flags.split())
            LoggingUtils.debug("Running command {}".format(' '.join(command)))
            response = subprocess.run(command, stdout=subprocess.PIPE)

            if response.returncode != 0:
                error_occured = True
                LoggingUtils.warning("There was an error when uploading to {}".format(dest))

        if error_occured:
            raise RcloneUploadError("An error occured when rclone was uploading a file",
                                    response.stdout.decode('utf-8'),
                                    job.episode,
                                    dest)

    @staticmethod
    def download(job: Job, sources: List[str], tempfolder: str, flags: str) -> str:
        """
        Download the provided episode from sources
        Returns the path of the downloaded file

        job: Job to do!
        sources: list of rclone sources (EncoderConf.downloading_sources)
        tmppath: Path of the temporary folder
        flags: rclone flags
        """

        # Step 1: Download the episode if possible
        dl_source = None
        for source in sources:
            if Rclone._check_episode_exists(job, source):
                LoggingUtils.debug("Found episode in source {}, downloading...".format(source), color=LoggingUtils.GREEN)
                dl_source = source
                break
        # If the file was not found in any sources, return False for failure
        if not dl_source:
            raise RcloneDownloadNotFoundError("No sources contained the episode, cancelling operation",
                                                "", job.show, job.episode)

        # Download the episode
        tempfolder = PathUtils.clean_directory_path(tempfolder)
        episode_src_file = Rclone._download_episode(job, dl_source, tempfolder, flags)

        return episode_src_file

    @staticmethod
    def _download_episode(job: Job, source: str, tempfolder: str, flags: str) -> str:
        """Helper to download file from remote to local temp"""
        # Note 1: The file will always ben downloaded as "temp.mkv"
        rclone_src_file = source + PathUtils.clean_directory_path(job.show) + job.episode
        rclone_dest_file = tempfolder + "temp.mkv"
        LoggingUtils.debug("Sourcing file from \"{}\"".format(rclone_src_file))
        LoggingUtils.debug("Downloading to temp file at \"{}\"".format(rclone_dest_file), color=LoggingUtils.YELLOW)

        LoggingUtils.debug("Beginning download...", color=LoggingUtils.YELLOW)
        command = [BinUtils.rclone]
        # If running in Docker, we need to load the user's rclone.conf in the conf folder
        if DockerUtils.docker:
            LoggingUtils.debug("Docker mode detected, referencing rclone config in the conf folder", color=LoggingUtils.YELLOW)
            command.extend(["--config={}".format(DockerUtils.conf + "rclone.conf")])
        else:
            LoggingUtils.debug("Docker mode not detected, using system rclone config", color=LoggingUtils.YELLOW)
        command.extend(["copyto", rclone_src_file, rclone_dest_file])
        command.extend(flags.split())
        LoggingUtils.debug("Running command {}".format(' '.join(command)))
        response = subprocess.run(command, stdout=subprocess.PIPE)

        # If the copy failed, return None
        if response.returncode != 0:
            raise RcloneDownloadError("Unable to copy episode file to local folder using rclone", "", job.show, job.episode)

        LoggingUtils.debug("Download complete.", color=LoggingUtils.GREEN)
        return rclone_dest_file

    @staticmethod
    def _check_episode_exists(job: Job, source: str) -> bool:
        """Given a source, check if Job file exists in source"""
        LoggingUtils.debug("Checking for episode in source: {}".format(source))
        try:
            # Call rclone to check whether or not something exists
            command = [BinUtils.rclone]
            # If running in Docker, we need to load the user's rclone.conf in the conf folder
            if DockerUtils.docker:
                LoggingUtils.debug("Docker mode detected, referencing rclone config in the conf folder", color=LoggingUtils.YELLOW)
                command.extend(["--config={}".format(DockerUtils.conf + "rclone.conf")])
            else:
                LoggingUtils.debug("Docker mode not detected, using system rclone config", color=LoggingUtils.YELLOW)
            command.extend(["lsjson", "-R", source + job.show])

            LoggingUtils.debug("Running command {}".format(' '.join(command)))
            response = subprocess.run(command, stdout=subprocess.PIPE)
            # Get the episode list in that folder
            episode_list = json.loads(response.stdout.decode('utf-8'))
            # Check if our job episode exists
            for episode in episode_list:
                if episode['Name'] == job.episode:
                    LoggingUtils.debug("Found a match for episode in source {}".format(source))
                    return True
            LoggingUtils.debug("Didn't find a match for episode in source {}".format(source))
            return False
        # This except block is usually hit if the source provided doesn't exist.
        except:
            LoggingUtils.warning("An error occured while checking source {}, does it exist?".format(source))
            return False