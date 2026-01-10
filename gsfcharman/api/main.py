from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import StringConstraints

from gsfcharman.api.data import CharacterData, Database, LumnisData, PendingLogoutRequest, SafeToLogoutData

db: Database = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.load()
    yield
    db.save()


app = FastAPI(lifespan=lifespan)


@app.get("/debug")
def get_debug() -> dict[str, CharacterData]:
    return db.data


@app.get("/characters/{character_name}")
def get_character(character_name: Annotated[str, StringConstraints(to_lower=True)]) -> CharacterData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")
    return db.data[character_name]


@app.get("/characters/{character_name}/lumnis")
def get_character_lumnis(character_name: Annotated[str, StringConstraints(to_lower=True)]) -> Optional[LumnisData]:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")
    return db.data[character_name].lumnis


@app.get("/characters/{character_name}/safe-to-logout")
def get_character_logout_safety(
    character_name: Annotated[str, StringConstraints(to_lower=True)],
) -> Optional[SafeToLogoutData]:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")
    return db.data[character_name].logout_safety


@app.put("/characters/{character_name}")
def put_character(
    character_name: Annotated[str, StringConstraints(to_lower=True)], character_data: CharacterData
) -> CharacterData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")

    db.data[character_name] = character_data

    return db.data[character_name]


@app.put("/characters/{character_name}/lumnis")
def put_character_lumnis(
    character_name: Annotated[str, StringConstraints(to_lower=True)], lumnis_data: LumnisData
) -> LumnisData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")

    db.data[character_name].lumnis = lumnis_data
    return lumnis_data


@app.put("/characters/{character_name}/safe-to-logout")
def put_character_logout_safety(
    character_name: Annotated[str, StringConstraints(to_lower=True)], logout_safety_data: SafeToLogoutData
) -> SafeToLogoutData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")

    db.data[character_name].logout_safety = logout_safety_data
    return logout_safety_data


@app.put("/characters/{character_name}/pending-logout-requests")
def put_character_pending_logout_requests(
    character_name: Annotated[str, StringConstraints(to_lower=True)],
    pending_logout_request: PendingLogoutRequest,
) -> PendingLogoutRequest:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")

    db.data[character_name].pending_logout_request = pending_logout_request
    return pending_logout_request


@app.post("/characters/{character_name}", status_code=status.HTTP_201_CREATED)
def post_character(
    character_name: Annotated[str, StringConstraints(to_lower=True)], character_data: CharacterData
) -> CharacterData:
    if character_name in db.characters():
        raise HTTPException(status_code=409, detail=f"Character {character_name} already exists.")

    db.data[character_name] = character_data

    return db.data[character_name]
