import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# 1. Definição das Listas de Domínio
TIPOS_PERICIA = [
    "Roubo", "Furto", "Veículo Localizado (furtado ou roubado)", "Furto Qualificado (arrombamento)",
    "Furto em Interior de Veículo", "Furto de Energia Elétrica ou Termodinâmica", "Furto d'água",
    "Dano", "Dano Seguido de Lesão Corporal", "Violação de Domicílio", "Marca em Animal",
    "Exercício Arbitrário das Próprias Razões", "Tráfico de Entorpecentes", "Explosão (sem vítima)",
    "Incêndio (sem vítima)", "Pichação", "Violação de Sepultura", "Ameaça", "Maus Tratos de Animal",
    "Arremesso de Projétil", "Adulteração de Placa e/ou Lacre", "Receptação", "Desmanche de Veículos",
    "Estelionato", "Extorsão", "Homicídio", "Feminicídio", "Latrocínio e/ou Tentativa de Latrocínio", 
    "Suicídio", "Cadáver Encontrado", "Morte Aparentemente Natural", "Afogamento", "Ossada Encontrada", 
    "Aborto", "Feto Encontrado", "Infanticídio", "Local de Estupro e/ou Veículo Envolvido em Estupro", 
    "Tentativa de Homicídio", "Tentativa de Suicídio", "Disparo de Arma de Fogo", "Lesão Corporal", 
    "Eletroplessão", "Explosão (com vítima)", "Incêndio (com vítima)", "Abandono de Incapaz", 
    "Roubo Com Estupro"
] # Adicionei Feminicídio, conforme seu primeiro prompt

TIPOS_LOCAL = ["Pátio", "DP", "Residência", "Via Pública", "Estabelecimento Comercial", "Terreno Baldio", "Área Rural", "Hospital"]
DELEGACIAS = ["1ª DP", "2ª DP", "3ª DP", "DEAM (Mulher)", "DHPP (Homicídios)", "DRFC (Furtos)", "DCA (Criança e Adolescente)"]
TECNICAS = ["Empoamento", "Macrofotografia", "Luz forense/lanterna"]

# 2. Função do Motor de Regras para Prioridade
def calcular_prioridade(tipo, dom, idosa):
    prioridade_base = 0.15 # Padrão para crimes menores
    
    crimes_altissimos = ["Homicídio", "Feminicídio", "Latrocínio e/ou Tentativa de Latrocínio", 
                         "Tentativa de Homicídio", "Local de Estupro e/ou Veículo Envolvido em Estupro", 
                         "Roubo Com Estupro", "Infanticídio", "Feto Encontrado", "Abandono de Incapaz"]
    crimes_medios = ["Roubo", "Lesão Corporal", "Disparo de Arma de Fogo", "Dano Seguido de Lesão Corporal", 
                     "Explosão (com vítima)", "Incêndio (com vítima)", "Extorsão"]
    
    if tipo in crimes_altissimos:
        prioridade_base = 0.70
    elif tipo in crimes_medios:
        prioridade_base = 0.40
        
    # Agravantes
    if dom: prioridade_base += 0.15
    if idosa: prioridade_base += 0.15
    
    # Adicionar ruído para simular vida real (o modelo de ML terá que aprender o padrão)
    ruido = random.uniform(-0.05, 0.05)
    prioridade_final = prioridade_base + ruido
    
    # Garantir que fique entre 0 e 1
    return round(max(0.0, min(prioridade_final, 1.0)), 4)

# 3. Geração dos Dados
def gerar_dataset(num_linhas):
    dados = []
    data_inicial = datetime(2023, 1, 1)
    
    for _ in range(num_linhas):
        tipo = random.choice(TIPOS_PERICIA)
        local = random.choice(TIPOS_LOCAL)
        delegacia = random.choice(DELEGACIAS)
        
        # Gerar datas e horários aleatórios
        delta_tempo = timedelta(days=random.randint(0, 365), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        horario_exame = (data_inicial + delta_tempo).strftime("%Y-%m-%d %H:%M:%S")
        
        # Quantidades (Poisson distribution para parecer mais real)
        qtd_objetos = int(random.expovariate(1/3)) 
        qtd_fotos = int(random.expovariate(1/20)) + 5 # Minimo de 5 fotos
        qtd_fitas = int(random.expovariate(1/2))
        
        # Técnicas (Pode ser uma ou mais)
        num_tecnicas = random.randint(1, len(TECNICAS))
        tecnicas_usadas = ", ".join(random.sample(TECNICAS, k=num_tecnicas))
        
        # Variáveis Booleanas (Logica para fazer sentido: feminicídio/lesão = maior chance de doméstica)
        violencia_domestica = True if (tipo in ["Feminicídio", "Lesão Corporal", "Ameaça"] and random.random() > 0.3) else random.choice([True, False])
        vitima_idosa = random.choice([True, False, False]) # Menor probabilidade de ser idoso (33%)
        
        # Calcula a Label (Target)
        prioridade = calcular_prioridade(tipo, violencia_domestica, vitima_idosa)
        
        dados.append([
            tipo, local, qtd_objetos, qtd_fotos, qtd_fitas, horario_exame, 
            delegacia, tecnicas_usadas, violencia_domestica, vitima_idosa, prioridade
        ])
        
    colunas = [
        "Tipo_Pericia", "Tipo_Local", "Qtd_Objetos", "Qtd_Fotos", "Qtd_Fitas", 
        "Horario_Exame", "Delegacia", "Tecnica_Utilizada", "Violencia_Domestica", 
        "Vitima_Idosa", "Classificacao_Prioridade"
    ]
    return pd.DataFrame(dados, columns=colunas)

# 4. Executar e salvar
if __name__ == "__main__":
    tamanho_dataset = 5000  # Quantidade de registros
    df = gerar_dataset(tamanho_dataset)

    diretorio_saida = Path(__file__).resolve().parent.parent / "data"
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    nome_base = "dataset_pericias_criminais"
    caminho_saida = diretorio_saida / f"{nome_base}.csv"
    contador = 1
    while caminho_saida.exists():
        caminho_saida = diretorio_saida / f"{nome_base}_{contador}.csv"
        contador += 1

    df.to_csv(caminho_saida, index=False, encoding='utf-8')
    print(f"Dataset gerado com sucesso! Shape: {df.shape}")
    print(f"Salvo em: {caminho_saida}")
    print(df.head())