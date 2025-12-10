from app.router import game as _game
from app.router import game_transaction as _gt
from app.router import cards as _cards

# expose primary router (game); other routers can be included individually if needed
router = _game.router
