from pydantic import BaseModel, constr
from pydantic import Field

class NewPlayer(BaseModel):
    lobby_name: constr(min_length=1, max_length=20)
    team_name: constr(min_length=1, max_length=20)
    player_name: constr(min_length=1, max_length=20)

# class Move(BaseModel):
#     move: constr(regex=r'^(UP|DOWN|LEFT|RIGHT)$')

# class Start(BaseModel):
#     start: constr(regex=r'^(START)$') 


class Move(BaseModel):
    move: str = Field(..., pattern=r'^(UP|DOWN|LEFT|RIGHT)$')

class Start(BaseModel):
    start: str = Field(..., pattern=r'^(START)$')