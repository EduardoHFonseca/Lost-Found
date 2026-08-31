import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database import Base


class LoteIngestao(Base):
    __tablename__ = "lotes_ingestao"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String(255), nullable=False)
    data_importacao = Column(DateTime, default=datetime.datetime.utcnow)
    total_linhas = Column(Integer, default=0)
    total_validos = Column(Integer, default=0)
    total_inconsistentes = Column(Integer, default=0)
    total_isentos_pf = Column(Integer, default=0)
    status_lote = Column(String(50), default="PROCESSANDO")  # PROCESSANDO, CONCLUIDO, EM_MEDIACAO

    anunciantes = relationship("Anunciante", back_populates="lote", cascade="all, delete-orphan")


class Anunciante(Base):
    __tablename__ = "anunciantes"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lotes_ingestao.id", ondelete="SET NULL"), nullable=True)

    # Campos Originais do CSV
    cod_anunciante_razao = Column(String(50), nullable=True)
    anunciante_rz_social = Column(String(255), nullable=True)
    cnpj_original = Column(String(50), nullable=True)
    cod_anunc_fantasia = Column(String(50), nullable=True)
    anunciante_fantasia = Column(String(255), nullable=True)

    # Campos Normalizados e Validados
    cnpj_limpo = Column(String(14), nullable=True, index=True)
    cnpj_formatado = Column(String(18), nullable=True)
    eh_matriz = Column(Boolean, nullable=True)
    cnpj_matriz_sugerido = Column(String(18), nullable=True)
    situacao_cadastral = Column(String(50), nullable=True)
    razao_social_receita = Column(String(255), nullable=True)
    nome_fantasia_receita = Column(String(255), nullable=True)
    cnae_principal = Column(String(255), nullable=True)
    uf = Column(String(2), nullable=True)

    # Controle e Workflow
    status_validacao = Column(String(50), default="PENDENTE")  # VALIDO_OK, CORRIGIDO_AUTO, REQUER_MEDIACAO, RESOLVIDO_MANUAL, ISENTO_PF
    tipo_divergencia = Column(String(100), nullable=True)      # FILIAL_EM_RAIZ, CNPJ_DUPLICADO_OUTRA_RAZAO, CNPJ_INATIVO, SEM_CNPJ, RAZAO_DIVERGENTE
    data_ultima_atualizacao = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    lote = relationship("LoteIngestao", back_populates="anunciantes")
    mediacoes = relationship("MediacaoOperador", back_populates="anunciante", cascade="all, delete-orphan")


class ConsultaCNPJCache(Base):
    __tablename__ = "consultas_cnpj_cache"

    cnpj_limpo = Column(String(14), primary_key=True, index=True)
    dados_json = Column(JSON, nullable=False)
    situacao_cadastral = Column(String(50), nullable=True)
    eh_matriz = Column(Boolean, nullable=True)
    cnpj_matriz = Column(String(14), nullable=True)
    razao_social = Column(String(255), nullable=True)
    nome_fantasia = Column(String(255), nullable=True)
    data_consulta = Column(DateTime, default=datetime.datetime.utcnow)


class MediacaoOperador(Base):
    __tablename__ = "mediacoes_operador"

    id = Column(Integer, primary_key=True, index=True)
    anunciante_id = Column(Integer, ForeignKey("anunciantes.id", ondelete="CASCADE"), nullable=False)
    opcao_escolhida = Column(String(50), nullable=False) # ALTERAR_CODIGO, UNIFICAR_ANUNCIANTES, MANTER_AMBOS, TROCAR_PARA_FILIAL, MARCAR_ISENTO
    cnpj_anterior = Column(String(18), nullable=True)
    cnpj_novo = Column(String(18), nullable=True)
    operador_id = Column(String(100), default="sistema")
    justificativa = Column(Text, nullable=True)
    data_decisao = Column(DateTime, default=datetime.datetime.utcnow)

    anunciante = relationship("Anunciante", back_populates="mediacoes")


class GrupoEconomico(Base):
    __tablename__ = "grupos_economicos"

    id = Column(Integer, primary_key=True, index=True)
    nome_grupo = Column(String(255), unique=True, index=True, nullable=False)
    cnpj_holding = Column(String(18), nullable=True)
    descricao = Column(Text, nullable=True)
    data_cadastro = Column(DateTime, default=datetime.datetime.utcnow)

    marcas = relationship("MarcaProduto", back_populates="grupo", cascade="all, delete-orphan")


class LoteMarca(Base):
    __tablename__ = "lotes_marcas"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String(255), nullable=False)
    data_importacao = Column(DateTime, default=datetime.datetime.utcnow)
    total_linhas = Column(Integer, default=0)
    total_mapeados = Column(Integer, default=0)
    total_pendentes = Column(Integer, default=0)
    status_lote = Column(String(50), default="CONCLUIDO")

    marcas = relationship("MarcaProduto", back_populates="lote", cascade="all, delete-orphan")


class MarcaProduto(Base):
    __tablename__ = "marcas_produtos"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lotes_marcas.id", ondelete="SET NULL"), nullable=True)
    grupo_id = Column(Integer, ForeignKey("grupos_economicos.id", ondelete="SET NULL"), nullable=True)

    marca = Column(String(255), nullable=False, index=True)
    anunciante_fantasia = Column(String(255), nullable=False, index=True)
    grupo_informado = Column(String(255), nullable=True, index=True)

    cnpj_identificado = Column(String(18), nullable=True, index=True)
    cnpj_limpo = Column(String(14), nullable=True, index=True)
    razao_social_identificada = Column(String(255), nullable=True)
    eh_matriz = Column(Boolean, nullable=True)
    pertence_grupo = Column(Boolean, default=True)
    confianca_score = Column(Integer, default=100)
    status_mapeamento = Column(String(50), default="MAPEADO_OK") # MAPEADO_OK, REQUER_VALIDACAO, DIVERGENCIA_GRUPO
    origem_resolucao = Column(String(100), nullable=True) # DIRETORIO_SOCIETARIO, BASE_ANUNCIANTES, RECEITA_WS
    observacoes = Column(Text, nullable=True)
    data_atualizacao = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    grupo = relationship("GrupoEconomico", back_populates="marcas")
    lote = relationship("LoteMarca", back_populates="marcas")

