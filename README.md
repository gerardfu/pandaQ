# pandaQ
# Descripció
PandaQ es una pràctica que implementa instruccions SQL amb Pandas para realizar consultas sobre taules. Aquesta implementació utilitza la gramàtica definida en el fitxer pandaQ.g4 y un script en Python pandaQ.py.

# Requisits Previs
Antes de ejecutar PandaQ, asegúrate de tener las siguientes dependencias instaladas:

Python 3.x
antlr4-python3-runtime
Streamlit
Pots instalar les dependencies executant:

pip install antlr4-python3-runtime streamlit

# Compilació de la Gramática
Abans d'executar PandaQ, assegura't de tenir les següents dependències instal·lades:

antlr4 -Dlanguage=Python3 -no-listener -visitor pandaQ.g4
Aquesta comanda generarà els arxius Python necessaris per a la interpretació de la gramàtica.

# Execució de PandaQ
Un cop compilada la gramàtica, pots executar PandaQ amb la interfície Streamlit. Utilitza la següent comanda:

streamlit run pandaQ.py
Això iniciarà la interfície d'usuari en el teu navegador predeterminat.

# Ús de PandaQ
Consulta SQL a Pandas: Escriu consultes SQL a l'àrea de text proporcionada.
Execució: Fes clic al botó "Executar Consulta" per processar la consulta i visualitzar els resultats.
Exploració Interactiva: Utilitza les funcionalitats interactives de Streamlit per explorar i analitzar els resultats.
Exemple de Consulta: Per obtenir una vista prèvia, aquí tens un exemple de consulta SQL que pots executar en PandaQ:

```python {background-color: #f0f0f0;}
Copy code
select columna1, columna2
from taula
where condicio;
