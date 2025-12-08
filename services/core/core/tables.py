"""
Contains the database definition for Signosure.
"""

# tables.py
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
from typing import List, Optional

from sqlalchemy import BigInteger, Column
from sqlmodel import Field, Relationship, SQLModel, create_engine


class User(SQLModel, table=True):
    """
    Represents a user account. All user accounts --- researchers, data
    collectors, and annotators --- are stored in the same database, even across
    datasets.
    """

    id: int = Field(primary_key=True)
    """ Primary key for the `user` table. """

    email: str
    """
    User's email address. This is the only outward-facing identifier for an
    account --- usernames are not required or saved.
    """

    confirm_token: str
    """
    Randomly-generated token for a user to confirm their email address or reset
    their password.
    """

    confirm_exp: int = Field(sa_column=Column(BigInteger))
    """
    Token expiration date. After this time, the token is no longer accepted.
    """

    validated: bool
    """ Whether or not the user's email address has been confirmed. """

    oauth: bool
    """
    Future value to use if using OAuth-based authentication. For now, we will
    not be implementing OAuth.
    """

    pass_hash: str
    """
    The user's password, hashed and stored in the following format:
    `<algo>:<backend>:<iterations>:<salt>:<hash>`
    """

    admin: bool
    """
    Whether or not a user has admin permissions. All other permission checks
    are bypassed if this value is `True` for a user.
    """

    base_permissions: int
    """
    The user's unscoped permissions. These permissions apply system-wide.
    """

    scoped_permissions: List["Permission"] = Relationship(back_populates="user")
    """
    The user's scoped permissions. These permissions apply to a specific scope,
    so that a user doesn't have permissions across the entire system.
    """

    def has_permissions(self, mask: int) -> bool:
        """
        Verifies that the user has all permissions specified in an integer
        permission mask `mask`.

        Params:
            `mask`: (`int`) an integer mask of permissions

        Returns:
            (`bool`) `True` if the user has all permissions represented by
            `mask`, or is an admin; `False` otherwise
        """
        return self.admin or (self.base_permissions & mask == mask)

    def has_permissions_in_scope(
        self, scope: "PermissionScope", mask: int
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
        if self.admin:
            return True

        for user_scope in self.scoped_permissions:
            if user_scope.scope_id == scope.id:
                return user_scope.admin_in_scope or (
                    user_scope.permission_mask & mask == mask
                )

        return False


class PermissionScope(SQLModel, table=True):
    """
    A scope in which permissions can be assigned. Typically, this will be
    associated with a `Dataset`, but permission scopes can be reused freely.
    """

    id: int = Field(primary_key=True)
    """ Primary key for the `PermissionScope` table. """

    default_collection: int
    """
    The default permissions to assign to data collectors in this scope.
    """

    default_annotation: int
    """
    The default permissions to assign to annotators in this scope.
    """


class Permission(SQLModel, table=True):
    """The permissions for a user within a specific scope."""

    user_id: int = Field(foreign_key="user.id", primary_key=True)
    """
    The ID of the user which these permissions belong to. One half of the
    primary key for the `permission` table, along with `scope_id`.
    """

    scope_id: int = Field(foreign_key="permissionscope.id", primary_key=True)
    """
    The ID of the permission scope these permissions belong to. The second half
    of the primary key for the `permission` table, along with `user_id`.
    """

    admin_in_scope: bool
    """
    Whether or not `user` is an admin in this scope. If `True`, all permission
    checks will be bypassed, and some permissions are reserved for
    administrators.
    """

    permission_mask: int
    """
    The permissions `user` has in `scope`, represented as an integer mask.
    """

    user: User = Relationship(back_populates="scoped_permissions")
    """ The user (`User`) these permissions belong to. """

    scope: PermissionScope = Relationship()
    """ The scope (`PermissionScope`) these permissions are valid in. """


class DeviceCategory(SQLModel, table=True):
    """
    A category of devices, such as tablets or smartphones. Device classes are
    useful when needing to restrict data collection only to tablets or
    smartphones.
    """

    id: int = Field(primary_key=True)
    """ Primary key for the `devicecategory` table. """

    name: str
    """ The name of the device category """


class DeviceModel(SQLModel, table=True):
    """
    A specific model of devices, such as a Google Pixel 10 Pro. Device metadata
    is collected and attached to each collected video.
    """

    id: int = Field(primary_key=True)
    """ Primary key for the `devicemodel` tabel. """

    manufacturer: str
    """ The manufacturer of the device. """

    name: str
    """ The name of this device, supplied by the operating system. """

    type_id: int = Field(foreign_key="devicecategory.id")
    """ The ID of the category this device belongs to. """

    type: DeviceCategory = Relationship()
    """ The category this device belongs to. """


class Dataset(SQLModel, table=True):
    """
    Represents a dataset. All data collection, annotation, and processing is
    done within the context of a specific dataset.
    """

    id: int = Field(primary_key=True)
    """ Primary key for the `dataset` table. """

    name: str
    """
    The name of this dataset.
    """

    scope_id: int = Field(foreign_key="permissionscope.id")
    """
    The ID of the permission scope used to manage permissions for this dataset.
    """

    default_repetitions: int
    """
    The default number of examples that a user must give for each prompt. This
    can be manually overridden for each prompt via the `PromptAffinity` object.
    """

    prompts_required: int
    """
    The number of distinct prompts that a user must collect data for. Assuming
    this dataset has `n` distinct prompts (linked via `PromptAffinity`),
    - set `prompts_required >= n` or `prompts_required = 0` to require the
      user to collect data for all prompts.
    - set `0 < prompts_required < n` to randomly select `prompts_required`
      prompts that the user should complete. If `sequential_unique_prompts` is
      `True`, prompts will be assigned in order of ID to each new data
      collector.

    The user's progress with each prompt is tracked in the `CollectorActivity`
    table.
    """

    sequential_unique_prompts: bool
    """
    If `True`, each user will be assigned `prompts_required` prompts in
    sequential order, ordered by the prompts' IDs. Each prompt assignment is
    unique and cannot be repeated across users in this case. If there aren't
    enough prompts to assign `prompts_required` prompts to a new collector,
    they will be assigned all remaining prompts (or zero prompts if none are
    available). Users with zero prompts will not be able to proceed until more
    prompts are added.

    If `prompts_required` is changed mid-collection, or new prompts are added,
    they will be assigned to users who have insufficient prompts assigned,
    sorted by increasing user ID.
    """

    collector_code: str
    """
    An 8-letter alphanumeric code that users can input to automatically
    link up to the correct dataset. Autogenerated. Example value: D9HF-QX5Z
    """

    annotator_code: str
    """
    A 6-letter alphanumeric code that annotators can input to automatically
    link up to the correct dataset. Autogenerated. Example value: 7GM-D3C
    """

    collector_registration_open: bool
    """
    Whether or not new accounts can automatically register to provide
    data to this dataset.
    """

    annotator_registration_open: bool
    """
    Whether or not new accounts can automatically register to annotate
    data in this dataset.
    """

    collector_requires_approval: bool
    """
    Whether volunteers must be manually approved in order to contribute to
    this dataset.
    """

    annotator_requires_approval: bool
    """
    Whether volunteers must be manually approved in order to annotate this
    dataset.
    """

    permission_scope: PermissionScope = Relationship()
    """
    The permission scope (`PermissionScope`) used to manage permissions for
    this dataset. Permission scopes can be reused across datasets.
    """


class DeviceCategoryRestriction(SQLModel, table=True):
    """
    Represents a ban on data collection from an entire category of devices for
    a particular dataset.
    """

    dataset_id: int = Field(foreign_key="dataset.id", primary_key=True)
    """
    The ID of the dataset for which the given device category will be
    restricted.
    """

    category_id: int = Field(foreign_key="devicecategory.id", primary_key=True)
    """
    The ID of the device category to restrict from contributing to the dataset.
    """

    soft: bool
    """
    Whether this is a soft restriction. If `True`, then users can still submit
    data from the given device category, but they will be segregated from the
    main dataset for researchers to deal with separately.

    If the device model has a hard restriction, then this field will be
    ignored, and data from this device model cannot be submitted. (For example,
    a dataset with a soft restriction on tablets will not allow data from an
    iPad Pro if that device model has a hard restriction.)
    """

    dataset: Dataset = Relationship()
    """ The dataset to which this restriction applies. """

    category: DeviceCategory = Relationship()
    """ The category of devices for which this restriction will be enforced. """


class DeviceModelRestriction(SQLModel, table=True):
    """
    Represents a ban on data collection from a particular model of device, for
    a particular dataset.
    """

    dataset_id: int = Field(foreign_key="dataset.id", primary_key=True)
    """
    The ID of the dataset for which the given device model will be restricted.
    """

    model_id: int = Field(foreign_key="devicemodel.id", primary_key=True)
    """
    The ID of the device model to restrict from contributing to the dataset.
    """

    soft: bool
    """
    Whether this is a soft restriction. If `True`, then users can still submit
    data from the given device model, but they will be segregated from the main
    dataset for researchers to deal with separately.

    If the device's category has a hard restriction, then this field will be
    ignored, and data from this device model cannot be submitted. (For example,
    a dataset with a hard restriction on tablets will not allow data from an
    iPad Pro, even if that specific device has a soft restriction.)
    """

    dataset: Dataset = Relationship()
    """ The dataset to which this restriction applies. """

    model: DeviceModel = Relationship()
    """ The device model for which this restriction will be enforced. """


class Prompt(SQLModel, table=True):
    """
    Represents a prompt that can be presented to a user to collect. Note that
    prompts can be reused across datasets, and their relationship to a dataset
    is denoted by the `PromptAffinity` class.
    """

    id: int = Field(primary_key=True)
    """ Primary key for the `prompt` table. """

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

    deleted: bool
    """
    Whether or not this prompt has been inactivated. To preserve data, prompts
    cannot be fully deleted, only deactivated.
    """

    def get_reference_filename(self) -> str:
        """
        Returns the file path for the reference video or photo shown to the user
        when displaying this prompt.

        TODO: Implement support for other file types and arbitrary storage
        locations.
        """
        filename = f"{self.id}.mp4"
        raise NotImplementedError


class PromptAffinity(SQLModel, table=True):
    """
    Represents the assignment of a prompt to a particular dataset.
    """

    dataset_id: int = Field(foreign_key="dataset.id", primary_key=True)
    """
    The ID of the dataset `prompt` is being assigned to. The first half of the
    primary key for `promptaffinity`.
    """

    prompt_id: int = Field(foreign_key="prompt.id", primary_key=True)
    """
    The ID of the prompt being assigned to `dataset`. The second half of the
    primary key for `promptaffinity`.
    """

    repetitions: int
    """
    The number of repetitions to assign to users for this prompt. If not
    specified, this will default to `default_repetitions` from the dataset.
    """

    dataset: Dataset = Relationship()
    """
    The dataset this prompt is assigned to.
    """

    prompt: Prompt = Relationship()
    """
    The prompt being assigned to a dataset.
    """


class CollectorAffinity(SQLModel, table=True):
    """
    An object indicating that a given user is a data collector for
    """

    user_id: int = Field(foreign_key="user.id", primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id", primary_key=True)

    user: User = Relationship()
    dataset: Dataset = Relationship()


class CollectorActivity(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id", primary_key=True)
    prompt_id: int = Field(foreign_key="prompt.id", primary_key=True)
    progress: int

    user: User = Relationship()
    dataset: Dataset = Relationship()
    prompt: Prompt = Relationship()


class CollectedVideo(SQLModel, table=True):
    id: int = Field(primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    dataset_id: int = Field(foreign_key="dataset.id")
    device_id: int = Field(foreign_key="devicemodel.id")
    filename: str = Field(max_length=64)

    author: User = Relationship()
    dataset: Dataset = Relationship()
    device: DeviceModel = Relationship()


class ReviewClass(SQLModel, table=True):
    id: int = Field(primary_key=True)
    label: str = Field(max_length=32)


class Annotation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    video_id: int = Field(foreign_key="collectedvideo.id")
    prompt_id: int = Field(foreign_key="prompt.id")
    auditor_id: int = Field(foreign_key="user.id")
    base_start: float
    base_end: float
    reviewed_start: Optional[float] = None
    reviewed_end: Optional[float] = None
    review_class_id: Optional[int] = Field(
        default=None, foreign_key="reviewclass.id"
    )
    review_comments: Optional[str] = Field(default=None, max_length=128)

    video: CollectedVideo = Relationship()
    prompt: Prompt = Relationship()
    auditor: User = Relationship()
    review_class: Optional[ReviewClass] = Relationship()


def init_databases(sqlite_file: str) -> None:
    sqlite_url = f"sqlite:///{sqlite_file}"
    engine = create_engine(sqlite_url, echo=True)
    SQLModel.metadata.create_all(engine)
