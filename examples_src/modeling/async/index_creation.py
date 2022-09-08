# ... Continuation of the previous snippet ...

from odmantic import AIOEngine

engine = AIOEngine()
await engine.configure_database([Product])
