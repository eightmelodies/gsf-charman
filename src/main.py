from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from data import CharacterData, Database, LumnisData, SafeToLogoutData

db: Database = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.load()
    yield
    db.save()


app = FastAPI(lifespan=lifespan)


@app.get("/characters/{character_name}")
def get_character(character_name: str) -> CharacterData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")
    return db.data[character_name]


@app.get("/characters/{character_name}/lumnis")
def get_character_lumnis(character_name: str) -> LumnisData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")
    return db.data[character_name].lumnis


@app.get("/characters/{character_name}/safe-to-logout")
def get_character_logout_safety(character_name: str) -> SafeToLogoutData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")
    return db.data[character_name].logout_safety


@app.put("/characters/{character_name}")
def put_character(character_name: str, character_data: CharacterData) -> CharacterData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")

    db.data[character_name] = character_data

    return db.data[character_name]


@app.put("/characters/{character_name}/lumnis")
def put_character_lumnis(character_name: str, lumnis_data: LumnisData) -> LumnisData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")

    db.data[character_name].lumnis = lumnis_data

    return db.data[character_name].lumnis


@app.put("/characters/{character_name}/safe-to-logout")
def put_character_logout_safety(character_name: str, logout_safety_data: SafeToLogoutData) -> SafeToLogoutData:
    if character_name not in db.characters():
        raise HTTPException(status_code=404, detail=f"Character {character_name} not found.")

    db.data[character_name].logout_safety = logout_safety_data

    return db.data[character_name].logout_safety


@app.post("/characters/{character_name}")
def post_character(character_name: str, character_data: CharacterData) -> CharacterData:
    if character_name in db.characters():
        raise HTTPException(status_code=409, detail=f"Character {character_name} already exists.")

    db.data[character_name] = character_data

    return db.data[character_name]
