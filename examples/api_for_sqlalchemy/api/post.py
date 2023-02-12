from http import HTTPStatus
from typing import (
    List,
    Union,
)

from fastapi import Depends
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from starlette import status
from tortoise.exceptions import DoesNotExist

from examples.api_for_sqlalchemy.extensions.sqlalchemy import Connector
from examples.api_for_sqlalchemy.helpers.factories.meta_base import FactoryUseMode
from examples.api_for_sqlalchemy.helpers.factories.post import PostFactory, ErrorCreatePostObject
from examples.api_for_sqlalchemy.helpers.updaters.exceptions import ObjectNotFound
from examples.api_for_sqlalchemy.helpers.updaters.update_post import UpdatePost, ErrorUpdatePostObject
from fastapi_rest_jsonapi import SqlalchemyEngine
from fastapi_rest_jsonapi.exceptions import (
    BadRequest,
    HTTPException,
)
from fastapi_rest_jsonapi.querystring import QueryStringManager
from fastapi_rest_jsonapi.schema import JSONAPIResultListSchema, JSONAPIResultListMetaSchema, JSONAPIResultDetailSchema
from fastapi_rest_jsonapi.views.detail_view import DetailViewBase
from fastapi_rest_jsonapi.views.list_view import ListViewBase

from examples.api_for_sqlalchemy.models import Post
from examples.api_for_sqlalchemy.models.schemas import (
    PostSchema,
    PostInSchema,
    PostPatchSchema,
)


class PostDetail(DetailViewBase):
    async def get(
        self,
        obj_id,
        query_params: QueryStringManager,
        session: AsyncSession = Depends(Connector.get_session),
    ) -> JSONAPIResultDetailSchema:
        dl = SqlalchemyEngine(
            schema=self.jsonapi.schema_detail,
            model=self.jsonapi.model,
            session=session,
        )
        view_kwargs = {"id": obj_id}
        return await self.get_detailed_result(
            dl=dl,
            view_kwargs=view_kwargs,
            query_params=query_params,
        )

    # @classmethod
    # async def patch(cls, obj_id, data: PostPatchSchema, query_params: QueryStringManager,
    #                 session: AsyncSession = Depends(Connector.get_session)) -> PostSchema:
    #     post_obj: Post
    #     try:
    #         post_obj = await UpdatePost.update(
    #             obj_id,
    #             data.dict(exclude_unset=True),
    #             query_params.headers,
    #             session=session,
    #         )
    #     except ErrorUpdatePostObject as ex:
    #         raise BadRequest(ex.description, ex.field)
    #     except ObjectNotFound as ex:
    #         raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=ex.description)
    #
    #     post = PostSchema.from_orm(post_obj)
    #     return post


class PostList(ListViewBase):
    async def get(
        self,
        query_params: QueryStringManager,
        session: AsyncSession = Depends(Connector.get_session),
    ) -> JSONAPIResultListSchema:
        dl = SqlalchemyEngine(
            schema=self.jsonapi.schema_list,
            model=self.jsonapi.model,
            session=session,
        )
        return await self.get_paginated_result(
            dl=dl,
            query_params=query_params,
        )

    async def post(
        self,
        data: PostInSchema,
        query_params: QueryStringManager,
        session: AsyncSession = Depends(Connector.get_session),
    ) -> JSONAPIResultDetailSchema:
        try:
            post_obj = await PostFactory.create(
                data=data.dict(),
                mode=FactoryUseMode.production,
                header=query_params.headers,
                session=session,
            )
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                # detail=str(e),
            )
        except ErrorCreatePostObject as ex:
            raise BadRequest(ex.description, ex.field)

        dl = SqlalchemyEngine(
            schema=self.jsonapi.schema_detail,
            model=self.jsonapi.model,
            session=session,
        )
        view_kwargs = {"id": post_obj.id}
        return await self.get_detailed_result(
            dl=dl,
            view_kwargs=view_kwargs,
            query_params=query_params,
        )
