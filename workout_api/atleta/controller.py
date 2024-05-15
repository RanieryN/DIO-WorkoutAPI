from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate
from workout_api.atleta.models import AtletaModel
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency

router = APIRouter()


@router.post(
    '/', 
    summary='Criar um novo atleta',
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut
)
async def post(
    db_session: DatabaseDependency, 
    atleta_in: AtletaIn = Body(...)
):
    categoria_nome = atleta_in.categoria.nome
    centro_treinamento_nome = atleta_in.centro_treinamento.nome

    categoria = (await db_session.execute(
        select(CategoriaModel).filter_by(nome=categoria_nome))
    ).scalars().first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f'A categoria {categoria_nome} não foi encontrada.'
        )
    
    centro_treinamento = (await db_session.execute(
        select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_nome))
    ).scalars().first()
    
    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f'O centro de treinamento {centro_treinamento_nome} não foi encontrado.'
        )
    try:
        atleta_out = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={'categoria', 'centro_treinamento'}))

        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id
        
        db_session.add(atleta_model)
        await db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, 
            detail=f'Já existe um atleta cadastrado com o cpf: {atleta_in.cpf}'
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Ocorreu um erro ao inserir os dados no banco'
        )

    return atleta_out


@router.get(
    '/', 
    summary='Consultar todos os Atletas',
    status_code=status.HTTP_200_OK,
    response_model=list[dict],
)
async def query_all(
    db_session: DatabaseDependency,
    limit: int = Query(10, description='Número máximo de itens por página'),
    offset: int = Query(0, description='Índice de deslocamento para a próxima página')
) -> list[dict]:
    query = select(AtletaModel)
    query = query.limit(limit).offset(offset)
    
    atletas = (await db_session.execute(query)).scalars().all()
    
    atletas_response = []
    for atleta in atletas:
        atleta_dict = {
            'nome': atleta.nome,
            'centro_treinamento': atleta.centro_treinamento.nome,
            'categoria': atleta.categoria.nome
        }
        atletas_response.append(atleta_dict)
    
    return atletas_response


@router.get(
    '/search', 
    summary='Pesquisar Atleta por nome ou CPF',
    status_code=status.HTTP_200_OK,
    response_model=list[dict],
)
async def query_by_name_or_cpf(
    db_session: DatabaseDependency,
    nome: str = Query(None, description='Nome do atleta para pesquisa'),
    cpf: str = Query(None, description='CPF do atleta para pesquisa'),
    limit: int = Query(10, description='Número máximo de itens por página'),
    offset: int = Query(0, description='Índice de deslocamento para a próxima página')
) -> list[dict]:
    query = select(AtletaModel)
    if nome:
        query = query.filter(AtletaModel.nome == nome)
    if cpf:
        query = query.filter(AtletaModel.cpf == cpf)
    
    query = query.limit(limit).offset(offset)
    
    atletas = (await db_session.execute(query)).scalars().all()
    
    atletas_response = []
    for atleta in atletas:
        atleta_dict = {
            'nome': atleta.nome,
            'centro_treinamento': atleta.centro_treinamento.nome,
            'categoria': atleta.categoria.nome
        }
        atletas_response.append(atleta_dict)
    
    if not atletas_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail='Nenhum atleta encontrado com o critério fornecido.'
        )
    
    return atletas_response



@router.get(
    '/{id}', 
    summary='Consultar um Atleta pelo ID',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query_by_id(
    id: UUID4,
    db_session: DatabaseDependency
) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado com o ID: {id}'
        )
    
    return atleta


@router.patch(
    '/{id}', 
    summary='Editar um Atleta pelo ID',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def patch(
    id: UUID4,
    db_session: DatabaseDependency,
    atleta_up: AtletaUpdate = Body(...)
) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado com o ID: {id}'
        )
    
    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta


@router.delete(
    '/{id}', 
    summary='Deletar um Atleta pelo ID',
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete(
    id: UUID4,
    db_session: DatabaseDependency
) -> None:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado com o ID: {id}'
        )
    
    await db_session.delete(atleta)
    await db_session.commit()