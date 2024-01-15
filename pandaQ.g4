
grammar pandaQ;
root : sqlStatement EOF            
     ;
sqlStatement : (ID ':=')? query ';'     # sqlStatementQuery
             | 'plot' ID  ';'           # sqlStatementPlot
             ;
query : 'select' ('*' | columnes) 'from' ID innerJoinStatement whereStatement orderStatement  
      ;
columnes : columna (',' columna)*  # columns
         ;
columna : ID                      # column
        | expr 'as' ID            # columnCalc
        ;
innerJoinStatement : ('inner join' ID 'on' ID OP_LOG ID)*   # innerJoin
                   ;
whereStatement : 'where' condicio  # where
               |                   # whereBuit
               ;
orderStatement : 'order' 'by' columnesOrd  # orderSt
               |                           # orderBuit
               ;
columnesOrd : columna ordre (',' columna ordre)*  # columnsOrd
            ;
ordre : ('[' ('ASC' | 'DESC') ']')?  # order
      ;
condicio : '(' condicio ')'           # condParen
         | 'not' condicio             # condNot
         | condicio 'and' condicio    # condAnd
         | condicio 'or' condicio     # condOr 
         | ID OP_LOG NUM              # condOp1
         | NUM OP_LOG ID              # condOp2
         | ID OP_LOG ID               # condOp3
         | ID 'in' '(' query ')'      # condIn
         ;

expr : '(' expr ')'           # exprParen
     | expr ('*' | '/') expr  # exprMultDiv
     | expr ('+' | '-') expr  # exprSumaResta
     | ID                     # exprCol
     | NUM                    # exprNum
     ;

ID : [a-zA-Z_]+ ;
NUM : [0-9]+ ('.' [0-9]+)? ;
OP_LOG : '<' | '=' ;
WS  : [ \t\n\r]+ -> skip ;