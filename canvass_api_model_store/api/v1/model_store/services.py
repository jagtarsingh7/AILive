"""Module containing services for model routes.

This module provides functions for creating a new model, selecting, updating,
retrieving and deleting a model.

Functions:
    create_model: Function to create a new model.
    model_selector: Function to select a model.
    delete_model: Function to delete a model.
    update_model: Function to update a model.

Attributes:
    oauth2schema: OAuth2PasswordBearer object for token authentication.
    JWT_SECRET: Secret key for JSON Web Token authentication.
    TOKEN_TYPE: Token type for JSON Web Token authentication.
"""

import logging
import os

import models.models as _models
import models.schemas as _schemas
from fastapi import HTTPException, security, status
from sqlalchemy import orm

oauth2schema = security.OAuth2PasswordBearer(tokenUrl="/auth/api/token")

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET")
TOKEN_TYPE = os.environ.get("TOKEN_TYPE")


async def update_model(
    user: _schemas.User, db: orm.Session, model: _schemas.ModelUpdate, model_id: int
):
    """Function to update a model.

    Args:
        user (_schemas.User): The user object.
        db (orm.Session): The database session object.
        model (_schemas.ModelUpdate): The update model object.
        model_id (int): The model id.

    Returns:
        _schemas.Model: The updated model object.

    Raises:
        HTTPException: If the model does not exist or if there is an internal server error.
    """
    try:
        # Find if model for user exists
        db_model = await model_selector(model_id, user, db)

        # Update model with new values
        for attr in model.__dict__.keys():
            if (
                hasattr(db_model, attr)
                and hasattr(model, attr)
                and getattr(model, attr) is not None
                and attr != "model_version"
            ):
                setattr(db_model, attr, getattr(model, attr))

        # Auto increment model version
        db_model.model_version += 1

        # Commit the changes to the database
        db.commit()
        db.refresh(db_model)

        # Return updated model
        return _schemas.Model.from_orm(db_model)
    except HTTPException as e:
        logger.exception(f"Model not found: {e}")
        raise e
    except Exception as e:
        logger.exception(f"Internal Server Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}"
        )


async def model_selector(model_id: int, user: _schemas.User, db: orm.Session):
    """Function to select a model.

    Args:
        model_id (int): The ID of the model to be selected.
        user (_schemas.User): The user object.
        db (orm.Session): SQLAlchemy database session object.

    Returns:
        The selected model object.

    Raises:
        HTTPException: If the model does not exist.
    """
    try:
        model = (
            db.query(_models.Model)
            .filter_by(user_id=user.id)
            .filter(_models.Model.id == model_id)
            .one()
        )
    except orm.exc.NoResultFound as e:
        logger.exception(f"Error: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    except Exception as e:
        logger.exception(f"Internal Server Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {e}"
        )

    return model
