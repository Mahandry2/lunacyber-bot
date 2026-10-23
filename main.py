from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Luna Cyber MikroTik Bot & Mini App is online!"}
