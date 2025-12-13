"""
Contains the MongoDB collection definitions for Signosure.
"""

# collections.py
# This file is part of Signosure.
#
# Copyright (c) 2025 Georgia Institute of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from beanie import Document
from pydantic import BaseModel

from core.permissions import ScopedPermission, UnscopedPermission


class User(Document):
    """
    Represents a user account. All user accounts --- researchers, data
    collectors, and annotators --- are stored in the same database, even across
    datasets.
    """

    email: str
    """ User's email address. """

    name: Optional[str] = None
    """ User's name. Usually optional, but can be required by researchers. """

    confirm_token: Optional[str] = None
    """ Token for a user to confirm their email address. """

    confirm_exp: Optional[int] = 0
    """ The time at which the user's email confirmation token expires. """

    validated: bool
    """ Whether or not the user's email address has been confirmed. """

    reset_token: Optional[str] = None
    """ Token for a user to reset their password. """

    reset_exp: Optional[int] = 0
    """ The time at which the user's password reset token expires. """

    oauth: Optional[bool] = False
    """ `(Not implemented)` Whether the account was registered via OAuth. """

    pass_hash: str
    """
    The user's password, hashed and stored in the following format:
    `<algo>:<backend>:<iterations>:<salt>:<hash>`.
    """

    admin: bool
    """
    Whether or not this user has admin permissions. All other permissions checks
    for this user are bypassed if this value is `True`.
    """

    unscoped_permissions: int = 0
    """
    The user's unscoped permissions. These permissions apply system-wide.
    """

    admin_scopes: Set[str] = set()
    """
    The scopes in which this user has admin permissions. All other permissions
    checks for this user are bypassed in a `PermissionScope` if this user's
    `admin_scopes` set contains that permission scope. (Scopes are stored as
    a list of string document IDs.)
    """

    scoped_permissions: Dict[str, int] = dict()
    """
    The permissions this user has in each scope. This object is a mapping from
    a `PermissionScope` ID to an integer permission mask. If a `PermissionScope`
    ID is not contained in this map, the user has no permissions in that scope.
    """

    activity_id: str
    """
    The string ID of the `UserActivity` object for this user. This object
    contains the user's progress in each dataset, and is separated for more
    efficient lookups.
    """

    def has_permissions(self, mask: UnscopedPermission) -> bool:
        """
        Verifies that the user has all permissions specified in an integer
        permission mask `mask`.

        Params:
            `mask`: (`int`) an integer mask of permissions

        Returns:
            (`bool`) `True` if the user has all permissions represented by
            `mask`, or is an admin; `False` otherwise
        """
        return (
            self.admin or UnscopedPermission(self.unscoped_permissions) in mask
        )

    def is_admin_in_scope(self, scope: "PermissionScope") -> bool:
        """
        Verifies that a user is an administrator in a given scope.

        Params:
            `scope`: (`PermissionScope`) the scope to check for the user.

        Returns:
            (`bool`) `True` if the user is an admin in `scope`, or is a
            system-wide admin; `False` otherwise.
        """
        return self.admin or str(scope.id) in self.admin_scopes

    def has_permissions_in_scope(
        self, scope: "PermissionScope", mask: ScopedPermission
    ) -> bool:
        """
        Verifies that the user has all permissions specified in an integer
        permission mask `mask`, for a given scope.

        Params:
            `mask`: (`int`) an integer mask of permissions
            `scope`: (`PermissionScope`) the scope to check for the user

        Returns:
            (`bool`) `True` if the user has all permissions represented by
            `mask` in `scope`, or is an admin either system-wide or in `scope`;
            `False` otherwise
        """
        scope_id = str(scope.id)
        if self.admin or scope_id in self.admin_scopes:
            return True

        if scope_id in self.scoped_permissions:
            scoped_mask = self.scoped_permissions[scope_id]
            return ScopedPermission(scoped_mask) in mask

        return False

    def permissions_in_any_scope(self):
        """
        Computes the union of permissions that a user has across all scopes.
        This is useful for determining which tabs the user in the web UI should
        be able to see.
        """
        if self.admin or len(self.admin_scopes) > 0:
            return ScopedPermission.ALL

        result = ScopedPermission.NONE

        for mask in self.scoped_permissions.values():
            result |= ScopedPermission(mask)

        return result


class UserActivity(Document):
    """
    The activity for a given user. All collection and annotation activity is
    separated into this document so that the base `User` object can be retrieved
    as efficiently as possible.
    """

    user_id: str
    """
    The ID of the user this activity belongs to.
    """

    collection_activity: Dict[str, "CollectorProgress"] = dict()
    """
    The user's collection activity in each dataset.
    """

    annotation_activity: Dict[str, "AnnotatorProgress"] = dict()
    """
    The user's annotation activity in each dataset.
    """


class Dataset(Document):
    """
    Represents a dataset. All data collection, annotation, and processing is
    done within the context of a specific dataset.
    """

    name: str
    """ The name of this dataset. """

    scope_id: str
    """
    The ID of the permission scope used to manage permissions for this dataset.
    """

    default_repetitions: int
    """
    The default number of examples that a user must give for each prompt. This
    can be manually overridden for each prompt via the `PromptAffinity` object.
    """

    prompts_assigned: int
    """
    The number of distinct prompts that a user must collect data for. Assuming
    this dataset has `n` distinct prompts (linked via `PromptAffinity`),
    - set `prompts_assigned >= n` or `prompts_assigned = 0` to require the
      user to collect data for all prompts.
    - set `0 < prompts_assigned < n` to randomly select `prompts_assigned`
      prompts that the user should complete. If `sequential_unique_prompts` is
      `True`, prompts will be assigned in order of ID to each new data
      collector.

    The user's progress with each prompt is tracked in the `CollectorActivity`
    table.
    """

    sequential_unique_prompts: bool
    """
    `(Not implemented)`

    If `True`, each user will be assigned `prompts_assigned` prompts in
    sequential order, ordered by the prompts' IDs. Each prompt assignment is
    unique and cannot be repeated across users in this case. If there aren't
    enough prompts to assign `prompts_assigned` prompts to a new collector,
    they will be assigned all remaining prompts (or zero prompts if none are
    available). Users with zero prompts will not be able to proceed until more
    prompts are added.

    If `prompts_assigned` is changed mid-collection, or new prompts are added,
    they will be assigned to users who have insufficient prompts assigned,
    sorted by increasing user ID.
    """

    collector_code: str
    """
    An 8-letter alphanumeric code that users can input to automatically
    link up to the correct dataset. Autogenerated. Example value: D9HF-QX5Z
    """

    collector_reg_open: bool
    """
    Whether or not new accounts can automatically register to provide
    data to this dataset.
    """

    collector_req_approval: bool
    """
    Whether volunteers must be manually approved in order to contribute to
    this dataset.
    """

    annotator_code: str
    """
    A 6-letter alphanumeric code that annotators can input to automatically
    link up to the correct dataset. Autogenerated. Example value: 7GM-D3C
    """

    annotator_reg_open: bool
    """
    Whether or not new accounts can automatically register to annotate
    data in this dataset.
    """

    annotator_req_approval: bool
    """
    Whether volunteers must be manually approved in order to annotate this
    dataset.
    """

    prompts: Set[str] = set()
    """
    The prompts assigned to this dataset. This is a list of string IDs for
    `Prompt` documents.
    """

    review_classifications: List[str]
    """
    The possible classifications that annotators can give. Annotators can also
    add comments alongside each reviewed example for more context.
    """

    device_bans: List["DeviceBan"]
    """
    A list of banned device models for this dataset.
    """

    contents: str
    """
    The string ID of the `DatasetContents` which contains the users, videos,
    and annotations for this dataset.
    """


class DatasetContents(Document):
    """
    Contains references to the contents of a dataset. This object is separated
    from the dataset in order to keep dataset metadata lookups quick.
    """

    dataset_id: str
    """
    The string ID of the dataset whose contents are contained in this document.
    """

    collector_ids: Set[str] = set()
    """
    The users who have collected data for this dataset, OR who have explicitly
    registered with a registration code, OR who have been explicitly added to
    this dataset by researchers. This list does NOT contain all user IDs that
    have permission to contribute to this dataset, as some of those users may
    never contribute, but we still want to know who is active in this dataset.
    """

    annotator_ids: Set[str] = set()
    """
    The users who have annotated data to this dataset, OR who have explicitly
    registered with an annotator code, OR who have been explicitly added to this
    dataset by researchers. This list does NOT contain all user IDs that have
    permission to annotate this dataset, as some of those users may never
    contribute, but we still want to know who is active in this dataset.
    """

    videos: List[str] = list()
    """
    A list of all videos collected for this dataset.
    """


class Video(Document):
    """
    Represents a video uploaded by an annotator.
    """

    author_id: str
    """ The ID of the user who contributed this data to the dataset. """

    dataset_id: str
    """ The ID of the dataset this video belongs to. """

    date: float
    """ The time at which this video was ingested into the system. """

    device_name: str
    """ The device model this video was recorded on. """

    filename: str
    """ The filename for the actual video file. """

    checksum: str
    """ The MD5 checksum for this video. """

    clips: List["Clip"]
    """
    A list of clips for this video. Note that `Clip` objects contain fields for
    both the original video and the reviewer's feedback, so this list will start
    with a list of labels and timestamps, and will end up also containing
    revised timestamps and the annotator's feedback (good/bad/variant/etc.).
    """


class Prompt(Document):
    """
    Represents a prompt that can be presented to a user to collect. Note that
    prompts can be reused across datasets.
    """

    internal_name: str
    """
    The normalized name for this prompt. This should avoid special characters
    like spaces or parentheses, as it will be used in filenames. Note that two
    prompts with the same internal_name can be assigned to the same dataset ---
    all filenames include the `id` field for disambiguation.
    """

    display_text: str
    """
    The display text for this prompt. This can be any string and is what is
    presented to the user.
    """

    filepath: Optional[str]
    """
    The filepath to the video or image that should be shown to the user when
    they are asked to sign this prompt, if any. Note that filepaths are
    deterministic based on the MongoDB object ID and cannot be arbitrary,
    but the filepath is stored here anyway since some files can be MP4s and some
    can be JPEGs.
    """


class PermissionScope(Document):
    """
    A scope in which permissions can be assigned. Typically, this will be
    associated with a single `Dataset`, but permission scopes can be reused
    freely.
    """

    default_collection: int = 0
    """ The default permissions for new data collectors in this scope. """

    default_annotation: int = 0
    """ The default permissions for new annotators in this scope. """


# Note: the classes below are not MongoDB documents, but are rather object types
# contained within the above documents. They extend Pydantic's BaseModel for
# automatic schema generation and serialization.


class PromptAssignment(BaseModel):
    """Represents a prompt being assigned to a user."""

    prompt_id: str
    """ The document ID for the `Prompt` the user has been assigned. """

    repetitions: int
    """ The number of times the user should be asked to sign this prompt. """

    progress: int = 0
    """ The number of times the user has already signed this prompt. """

    unsynced_progress: Optional[int] = 0
    """
    The amount of progress that a user has made on a local device that has
    not been synced to the server. This value resets to 0 on a local device
    whenever a sync completes and is always 0 from the server's perspective.
    """


class CollectorProgress(BaseModel):
    """
    Represents the user's progress when collecting data. This object should be
    synced between the server and the user's device.
    """

    prompts: List[PromptAssignment] = []
    """
    A list of prompts assigned to the user.
    """

    last_sync: datetime
    """
    The last time information was synced between the device and server.
    """

    def total_progress(self) -> Tuple[int, int]:
        """
        Gets the user's overall progress as a tuple of integers.

        Returns:
            `(int, int)`: a tuple with the following values:
            - the number of examples recorded by the user so far
            - the total number of examples the user has to record
        """
        progress, total = 0, 0
        for prompt in self.prompts:
            progress += prompt.progress
            total += prompt.repetitions

        return progress, total

    def reconcile(self, remote: "CollectorProgress") -> "CollectorProgress":
        """
        Syncs data from a remote device to `self`, and returns any data that the
        remote device may be missing.

        Params:
            - `remote`: (`CollectorProgress`) data from the remote device.

        Returns:
            (`CollectorProgress`) new information from the
        """
        # Step 1. Sync user's progress to the server.
        local_lookup = {str(x.prompt_id): x for x in self.prompts}
        result: List["PromptAssignment"] = list()

        for remote_prompt in remote.prompts:
            prompt_id = str(remote_prompt.prompt_id)

            # Ignore malformed data
            if prompt_id not in local_lookup:
                continue

            # Ignore data that is identical to the server
            local_prompt = local_lookup[prompt_id]
            if remote_prompt == local_prompt:
                continue

            if remote_prompt.unsynced_progress is not None:
                local_prompt.progress += remote_prompt.unsynced_progress

                # The `unsynced_data` field does not need to be returned to the
                # user's device, because it is always 0 after syncing.
                remote_prompt.unsynced_progress = None

        # Step 2. Form a response for missing data that needs to be returned to
        # the remote device. Note that the server does not keep track of what
        # data has been synced to the device, so this response will contain all
        # of the prompt data, minus the prompts that were sent to the server
        # for updates.
        remote_lookup = {str(x.prompt_id): x for x in remote.prompts}

        result: List["PromptAssignment"] = list()
        for server_prompt in self.prompts:
            prompt_id = str(server_prompt.prompt_id)

            # Prompt was not included in the sync request from the remote device
            if prompt_id not in remote_lookup:
                result.append(server_prompt)
                continue

            remote_prompt = remote_lookup[prompt_id]
            if server_prompt == remote_prompt:
                continue

            # Prompt has some different fields (repetitions and/or progress
            # changed)
            new_progress = (
                server_prompt.progress
                if server_prompt.progress > remote_prompt.progress
                else remote_prompt.progress
            )
            new_prompt = PromptAssignment(
                prompt_id=prompt_id,
                repetitions=server_prompt.repetitions,
                progress=new_progress,
            )

            result.append(new_prompt)

        return CollectorProgress(
            prompts=result,
            last_sync=datetime.now(),
        )


class AnnotatorProgress(BaseModel):
    """
    Represents an annotator's progress when annotating data.
    """

    pass


class Clip(BaseModel):
    """
    Represents a clip inside a video. This object includes both

    - the initial data generated when the user collects and uploads a video, and
    - the data generated by annotators when they review a video.
    """

    prompt_id: str
    """ The ID of the prompt contained in this clip. """

    base_start: float
    """ The original start time of this clip, in seconds. """

    base_end: float
    """ The original end time of this clip, in seconds. """

    annotator_id: Optional[str] = None
    """ The ID of the user who annotated this video. """

    classification: Optional[str] = None
    """
    The classification given to this clip (good/bad/variant/etc.). Possible
    values for this field are defined for each dataset, in the
    `review_classifications` array.
    """

    comment: Optional[str] = None
    """ A comment left by the annotator with more details. """

    revised_start: Optional[float] = None
    """ The annotator's revised start time for the clip. """

    revised_end: Optional[float] = None
    """ The annotator's revised start time for the clip. """


class DeviceBan(BaseModel):
    """
    Represents a restriction on collecting data from a certaint type of device.
    """

    model: str
    """ The device identifier, as reported by the device's operating system. """

    soft: bool = False
    """
    Whether the ban is a soft ban (`True`) or a hard ban (`False`). If `True`,
    volunteers can still submit data from these devices, but their data will be
    sequestered into a separate category. This can be useful if researchers want
    as much data as possible, but want to review the data coming out of certain
    devices to make sure it is high-quality enough. If `False`, volunteers will
    receive a message telling them that their device cannot be used for data
    collection.
    """
