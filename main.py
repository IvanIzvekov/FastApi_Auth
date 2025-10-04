from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound, IntegrityError, DataError, OperationalError
from contextlib import asynccontextmanager
from database import Base, engine
from routes import users, auth, roles_permissions

import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="BestOfTheBestAuth", lifespan=lifespan)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(roles_permissions.router)

@app.middleware("http")
async def error_handler_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except NoResultFound as exc:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc) or "Record not found"}
        )
    except IntegrityError as exc:
        return JSONResponse(
            status_code=409,
            content={"detail": str(getattr(exc, "orig", exc))}
        )
    except DataError as exc:
        return JSONResponse(
            status_code=400,
            content={"detail": str(getattr(exc, "orig", exc))}
        )
    except OperationalError as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": str(getattr(exc, "orig", exc))}
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Неизвестная ошибка: {str(exc)}"}
        )