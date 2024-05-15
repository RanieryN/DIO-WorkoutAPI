Para criar e utilizar o ambiente virtual padrão do Python (venv)

        python -m venv workoutapi

para entrar no ambiente virtual: 

        workoutapi\Scripts\activate
para executar

        make run
            ou
        uvicorn workout_api.main:app --reload


-----------------------------------------------------------------------------------
Caso o make make-migrations do arquivo Makefile não funcione

use o:

    alembic revision --autogenerate -m "teste"
                    e
    alembic upgrade head
