import streamlit as st
import pandas as pd
from antlr4 import *
from pandaQLexer import pandaQLexer
from pandaQParser import pandaQParser
from pandaQVisitor import pandaQVisitor
import shlex
import sys


# Funcions i classes externes per avaluar les estructures de dades que envia el visitor

class Expressio:
    def calcular(self, df):
        pass

class MultDiv(Expressio):
    def __init__(self, op, fill1, fill2):
        self.expr1 = fill1
        self.expr2 = fill2
        self.op = op
    def calcular(self, df):
        col1 = self.expr1.calcular(df)
        col2 = self.expr2.calcular(df)
        if (self.op == '*'):
            col = col1 * col2
        else:
            col = col1 / col2
        return col
    
class SumaResta(Expressio):
    def __init__(self, op, fill1, fill2):
        self.expr1 = fill1
        self.expr2 = fill2
        self.op = op
    def calcular(self, df):
        col1 = self.expr1.calcular(df)
        col2 = self.expr2.calcular(df)
        if (self.op == '+'):
            col = col1 + col2      
        else:
            col = col1 - col2
        return col
    
class Columna(Expressio):
    def __init__(self, nomCol):
        self.id = nomCol
    def calcular(self, df):
        return df[self.id]
    
class Numero(Expressio):
    def __init__(self, num):
        self.num = num
    def calcular(self, df):
        df['c'] = self.num
        return df['c']
    
class Buit(Expressio):
    def __init__(self):
        pass
    def calcular(self, df):
        pass
      
class Condicio:
    def filtrar(self, df):
        return df

class Not(Condicio):
    def __init__(self, fill):
        self.cond = fill
    def filtrar(self, df):
        dfn = self.cond.filtrar(df)
        diferencia_df_dfn = df.merge(dfn, how='left', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
        return diferencia_df_dfn

class And(Condicio):
    def __init__(self, fill1, fill2):
        self.cond1 = fill1
        self.cond2 = fill2
    def filtrar(self, df):
        df1 = self.cond1.filtrar(df)
        df2 = self.cond2.filtrar(df)
        return pd.merge(df1, df2, how='inner')
    
class Or(Condicio):
    def __init__(self, fill1, fill2):
        self.cond1 = fill1
        self.cond2 = fill2
    def filtrar(self, df):
        df1 = self.cond1.filtrar(df)
        df2 = self.cond2.filtrar(df)
        return pd.concat([df1, df2], ignore_index=True)

class Comparacio12(Condicio):
    def __init__(self, op, col, num, ordre):
        self.operador = op
        self.col = col
        self.num = num
        self.ordre = ordre
    def filtrar(self, df):
        if self.operador == '<':
           if self.ordre == 0:
              return df.loc[df[self.col] < self.num]
           else:
              return df.loc[self.num < df[self.col]]
        elif self.operador == '=':
           return df.loc[df[self.col] == self.num]
        
class Comparacio3(Condicio):
    def __init__(self, op, col1, col2):
        self.operador = op
        self.col1 = col1
        self.col2 = col2
    def filtrar(self, df):
        if self.operador == '<':
           return df.loc[df[self.col1] < df[self.col2]]
        elif self.operador == '=':
           return df.loc[df[self.col1] == df[self.col2]]

class CondIn(Condicio):
    def __init__(self, col, llista):
        self.llista = llista
        self.col = col
    def filtrar(self, df):
        if not self.col == '':
            return df[df[self.col].isin(self.llista[self.col])]
            
    
def ordenar(df, columnesOrd):
    llistaCol = columnesOrd[0]
    llistaAsc = columnesOrd[1]
    return df.sort_values(by=llistaCol, ascending=llistaAsc)
   
def unirTaules(df1, llistaTaules):
    for taula in llistaTaules:
        nomTaula = taula[0]
        nomCol1 = taula[1]
        nomCol2 = taula[2]
        file = 'data/' + nomTaula + '.csv'
        data = pd.read_csv(file)
        df2 = pd.DataFrame(data)
        df1 = pd.merge(df1, df2, left_on=nomCol1, right_on=nomCol2, how='inner')
    return df1


# Eval Visitor

class EvalVisitor(pandaQVisitor):
    def __init__(self):
        self.taula_simbols = {}

    def visitSqlStatementQuery(self, ctx):
        if ctx.getChildCount() > 2:        # amb assignació a una variable
            [variable, _, query, _] = list(ctx.getChildren())
            df = self.visit(query)
            self.taula_simbols[variable.getText()] = df
            st.dataframe(df)
        else:                              # sense assignació a una variable
            [query, _] = list(ctx.getChildren())
            df = self.visit(query)
            st.dataframe(df)

    def visitSqlStatementPlot(self, ctx):   # plot taula
        [plot, taula, _] = list(ctx.getChildren())
        nomTaula = taula.getText()
        if nomTaula in self.taula_simbols:
            df = self.taula_simbols[nomTaula]
            columnas_numeriques = df.select_dtypes(include=['int64', 'float64']).columns
            st.line_chart(df[columnas_numeriques])


    def visitQuery(self, ctx):              # query
        [select, camps, f, taula, innerJoinStatement, whereStatement, orderStatement] = list(ctx.getChildren())
        
        if taula.getText() in self.taula_simbols:
            df = self.taula_simbols[taula.getText()]
        else:
            file = 'data/' + taula.getText() + '.csv'
            data = pd.read_csv(file)
            df = pd.DataFrame(data)

        # unir taules (inner join)
        llistaTaules = self.visit(innerJoinStatement)
        df = unirTaules(df, llistaTaules)

        # llista de columnes a mostrar
        if camps.getText() == '*':
            llistaIDsCol = list(df.columns)
        else :
            (llistaIDsCol, columnesCalc) = self.visit(camps)
            for (nomCol, expr) in columnesCalc:
                col = expr.calcular(df)
                df[nomCol] = col

        # filtrar files (where) 
        condicio = self.visit(whereStatement)      # visitar where
        df = condicio.filtrar(df)

        # ordenar files (order by)
        columnesOrd = self.visit(orderStatement)   # visitar order by
        df = ordenar(df, columnesOrd)
        
        return df[llistaIDsCol]

    def visitColumns(self, ctx):
        llista = []
        llistaColumnesCalc = []
        col = ctx.getChild(0)
        (nomCol, expr) = self.visit(col)
        llista.append(nomCol)
        if not isinstance(expr, Buit):
              llistaColumnesCalc.append((nomCol, expr))
        for i in range(2, ctx.getChildCount(), 2):
           col = ctx.getChild(i)
           (nomCol, expr) = self.visit(col)
           llista.append(nomCol)
           if not isinstance(expr, Buit):
              llistaColumnesCalc.append((nomCol, expr))
        return (llista, llistaColumnesCalc)
    
    def visitColumnsOrd(self, ctx):
        llistaCol = []
        llistaAsc = []
        col = ctx.getChild(0)
        asc = ctx.getChild(1)
        (nomCol, _) = self.visit(col)
        boolAsc = self.visit(asc)
        llistaCol.append(nomCol)
        llistaAsc.append(boolAsc)
        for i in range(2, ctx.getChildCount(), 3):
           col = ctx.getChild(i+1)
           asc = ctx.getChild(i+2)
           (nomCol, _) = self.visit(col)
           boolAsc = self.visit(asc)
           llistaCol.append(nomCol)
           llistaAsc.append(boolAsc)
        return (llistaCol, llistaAsc)
            
    def visitColumn(self, ctx):
        [col] = list(ctx.getChildren())
        nomCol = col.getText()
        return (nomCol, Buit())
    
    def visitColumnCalc(self, ctx):
        [expr, as_, col] = list(ctx.getChildren())
        nomCol = col.getText()
        expressio = self.visit(expr)             
        return (nomCol, expressio)
    
    def visitInnerJoin(self, ctx):
        llista = []
        for i in range(0, ctx.getChildCount(), 6):
           taula = ctx.getChild(i+1).getText()
           col1 = ctx.getChild(i+3).getText()
           col2 = ctx.getChild(i+5).getText()
           llista.append((taula, col1, col2))
        return llista
    
    def visitOrderSt(self, ctx):
        [order, by, columnesOrd] = list(ctx.getChildren())
        return self.visit(columnesOrd)
    
    def visitOrderBuit(self, ctx):
        return ([], [])
    
    def visitWhere(self, ctx):
        [where, condicio] = list(ctx.getChildren())
        return self.visit(condicio)
    
    def visitWhereBuit(self, ctx):
        return Condicio()
   
    def visitOrder(self, ctx):
        if ctx.getChildCount() == 3:
           [c1, ord, c2] = list(ctx.getChildren())
           if ord.getText() == 'ASC':
              return True
           else:
              return False
        else:
           return True
    
    def visitExprParen(self, ctx):
        [paren1, expr, paren2] = list(ctx.getChildren())
        return self.visit(expr)
    
    def visitExprMultDiv(self, ctx):
        [expr1, op, expr2] = list(ctx.getChildren())
        fill1 = self.visit(expr1)
        fill2 = self.visit(expr2)
        return MultDiv(op.getText(), fill1, fill2)
    
    def visitExprSumaResta(self, ctx):
        [expr1, op, expr2] = list(ctx.getChildren())
        fill1 = self.visit(expr1)
        fill2 = self.visit(expr2)
        return SumaResta(op.getText(), fill1, fill2)
    
    def visitExprCol(self, ctx):
        [col] = list(ctx.getChildren())
        nomCol = col.getText()
        return Columna(nomCol)
    
    def visitExprNum(self, ctx):
        [num] = list(ctx.getChildren())
        return Numero(float(num.getText()))

    def visitCondParen(self, ctx):
        [paren1, cond, paren2] = list(ctx.getChildren())
        return self.visit(cond)
    
    def visitCondNot(self, ctx):
        [NOT, cond] = list(ctx.getChildren())
        fill = self.visit(cond)
        return Not(fill)

    def visitCondAnd(self, ctx):
        [cond1, AND, cond2] = list(ctx.getChildren())
        fill1 = self.visit(cond1)
        fill2 = self.visit(cond2)
        return And(fill1, fill2)
  
    def visitCondAnd(self, ctx):
        [cond1, OR, cond2] = list(ctx.getChildren())
        fill1 = self.visit(cond1)
        fill2 = self.visit(cond2)
        return OR(fill1, fill2)
    
    def visitCondOp1(self, ctx):
        [col, op, num] = list(ctx.getChildren())
        nomCol = col.getText()
        OP = (op.getText())[0]
        return Comparacio12(OP, nomCol, float(num.getText()), 0)
    
    def visitCondOp2(self, ctx):
        [num, op, col] = list(ctx.getChildren())
        nomCol = col.getText()
        OP = (op.getText())[0]
        return Comparacio12(OP, nomCol, float(num.getText()), 1)
    
    def visitCondOp3(self, ctx):
        [col1, op, col2] = list(ctx.getChildren())
        nomCol1 = col1.getText()
        nomCol2 = col2.getText()
        OP = (op.getText())[0]
        return Comparacio3(OP, nomCol1, nomCol2)
    
    def visitCondIn(self, ctx):
        [col, op, par1, query, par2] = list(ctx.getChildren())
        nomCol = col.getText()
        llista = self.visit(query)
        return CondIn(nomCol, llista)
    

def main():

    if 'visitor' not in st.session_state:
        st.session_state['visitor'] = EvalVisitor()

    st.title("PandaQ")     
    with st.form("my_form"):                        
        texto = st.text_area("Query:")              # Quadre de text per entrar la statement
        button = st.form_submit_button("Submit")    # Botó per processar statement
    
    if button:
        input_stream = InputStream(texto)
        lexer = pandaQLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = pandaQParser(token_stream)
        tree = parser.root()
        if parser.getNumberOfSyntaxErrors() == 0:
            try:
                st.session_state['visitor'].visit(tree)
            except TypeError:
                st.write("Error: operació entre tipus no vàlida")
            except FileNotFoundError:
                st.write("Error: la taula no existeix")
            except KeyError:
                st.write("Error: columna invàlida")
        else:
            st.write('Error en la sintaxi de la statement')
            print(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
            print(tree.toStringTree(recog=parser))
        

if __name__ == '__main__':
    main()



    