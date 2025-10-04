class UnauthorizedException(Exception):
    pass

class ForbiddenException(Exception):
    pass

class SessionCreateError(Exception):
    pass

class SessionDeactivateError(Exception):
    pass

class SessionGetError(Exception):
    pass

class UserCreateError(Exception):
    pass

class UserGetError(Exception):
    pass

class UserDeleteError(Exception):
    pass

class UserEmailExistsError(Exception):
    pass

class UserUpdateError(Exception):
    pass

class NotFoundError:
    pass

class RolePermissionNotFound(Exception):
    pass

class RoleGetError(Exception):
    pass

class RoleAlreadyExistsError(Exception):
    pass

class PermissionAlreadyExistsError(Exception):
    pass

class PermissionGetError(Exception):
    pass