"""
APIs for creating, updating, and deleting datasets.
"""

# datasets.py
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
import random
from typing import List, Optional, cast

from fastapi import APIRouter, Depends, Form, HTTPException

from core import config, logger
from core.auth import get_admin_user, get_current_active_user
from core.config import get_config_value
from core.mongodb import Dataset, DatasetContents, PermissionScope, User
from core.permissions import ScopedPermission, get_default_permissions

router = APIRouter()

REG_CODE_LENGTH = 8


def generate_registration_code(prefix: str):
    result = prefix

    letter = False
    while len(result) < REG_CODE_LENGTH - 1:
        choice = random.randint(0, 25 if letter else 9)
        result += chr(choice + ord("A" if letter else "0"))
        letter = not letter

    checksum = sum([ord(ch) for ch in result]) % 26
    check_letter = chr(checksum + ord("A"))

    return result + check_letter


@router.post(path="/validate-create")
async def validate_dataset_creation(
    name: str = Form(...), permission_scope: Optional[str] = Form(None)
):
    existing_dataset = await Dataset.find_one(Dataset.name == name)
    errors = list()
    if existing_dataset is not None:
        errors.append("datasets.new.name-in-use")

    if permission_scope:
        if not await PermissionScope.find_one(
            PermissionScope.id == permission_scope
        ):
            errors.append("datasets.new.invalid-permission-scope")

    if errors:
        logger.debug(f"reject /validate-create: {errors}")
        raise HTTPException(400, detail={"errors": errors})

    return {"valid": True}


@router.post(path="/create")
async def create_dataset(
    user: User = Depends(get_admin_user),
    name: str = Form(...),
    language: str = Form(...),
    region: str = Form(""),
    permission_scope: Optional[str] = Form(None),
    default_reps: Optional[int] = Form(None),
    prompts_per_user: Optional[int] = Form(None),
    sequential_unique_prompts: bool = Form(False),
    collector_open_registration: bool = Form(False),
    collectors_require_approval: bool = Form(True),
    annotator_open_registration: bool = Form(False),
    annotators_require_approval: bool = Form(True),
):
    """
    Creates a new dataset.
    """
    await validate_dataset_creation(name, permission_scope)

    coll_reg_code = ""
    if collector_open_registration:
        coll_reg_code = generate_registration_code("C")
        while (
            await Dataset.find_one(Dataset.collector_code == coll_reg_code)
            is not None
        ):
            coll_reg_code = generate_registration_code("C")

    anno_reg_code = ""
    if annotator_open_registration:
        anno_reg_code = generate_registration_code("A")
        while (
            await Dataset.find_one(Dataset.annotator_code == anno_reg_code)
            is not None
        ):
            anno_reg_code = generate_registration_code("A")

    if prompts_per_user is None:
        prompts_per_user = -1

    if not permission_scope:
        scope_obj = await PermissionScope.find_one(PermissionScope.name == name)
        if scope_obj is None:
            c_unscoped, c_scoped = get_default_permissions("collector")
            a_unscoped, a_scoped = get_default_permissions("annotator")
            scope_obj = PermissionScope(
                name=name,
                default_collection=c_scoped.value,
                default_unscoped_collection=c_unscoped.value,
                default_annotation=a_scoped.value,
                default_unscoped_annotation=a_unscoped.value,
            )

            await scope_obj.save()

        scope_obj = cast(PermissionScope, scope_obj)
        permission_scope = str(scope_obj.id)

    default_classifications = config.get_config_value(
        "datasets.default-classifications", List
    )

    if default_reps is None:
        default_reps = config.get_config_value(
            "datasets.default-repetitions", int
        )

    new_dataset = Dataset(
        name=name,
        language=language,
        region=region,
        scope_id=permission_scope,
        default_repetitions=default_reps,
        prompts_assigned=prompts_per_user,
        sequential_unique_prompts=sequential_unique_prompts,
        collector_code=coll_reg_code,
        collector_reg_open=collector_open_registration,
        collector_req_approval=collectors_require_approval,
        annotator_code=anno_reg_code,
        annotator_reg_open=annotator_open_registration,
        annotator_req_approval=annotators_require_approval,
        review_classifications=default_classifications,
        device_bans=list(),
        contents_id="",
    )

    await new_dataset.save()

    dataset_contents = DatasetContents(dataset_id=str(new_dataset.id))
    await dataset_contents.save()

    new_dataset.contents_id = str(dataset_contents.id)
    await new_dataset.save()

    return {"success": True, "id": str(new_dataset.id)}


@router.get(path="/list")
async def list_datasets(user: User = Depends(get_current_active_user)):
    datasets: List[Dataset] = list()

    # Admins have access to all datasets
    if user.admin:
        datasets = await Dataset.find_all().to_list()

    # Other users should only see datasets where they are an admin or have
    # view/edit permissions.
    else:
        all_associated_scopes = set(user.admin_scopes)
        for scope_id, mask in user.scoped_permissions.items():
            if ScopedPermission(mask) & ScopedPermission.WEB_VISIBILITY == 0:
                continue

            if scope_id not in all_associated_scopes:
                all_associated_scopes.add(scope_id)

        if all_associated_scopes:
            datasets = await Dataset.find(
                {"scope_id": {"$in": list(all_associated_scopes)}}
            ).to_list()

    return [
        {
            "id": str(dataset.id),
            "name": dataset.name,
            "language": dataset.language,
            "region": dataset.region,
        }
        for dataset in datasets
    ]
