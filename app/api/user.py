from app.router import user as _user
from app.router import api_user as _api_user

# expose both routers under single module for inclusion
router = _user.router
