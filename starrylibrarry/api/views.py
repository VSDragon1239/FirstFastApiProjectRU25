from typing import List

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404

# from .schemas import RegisterIn, UserOut, LoginIn, TokenPairOut, ItemIn, ItemOut, RoleIn

# from .models import Item

from ninja.errors import HttpError
from ninja_extra import NinjaExtraAPI, api_controller, route, permissions
from ninja_jwt.controller import NinjaJWTDefaultController, TokenVerificationController
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken


User = get_user_model()

api = NinjaExtraAPI(auth=None)
api.register_controllers(NinjaJWTDefaultController)
api.auth = [JWTAuth()]
