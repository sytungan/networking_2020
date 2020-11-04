from BKITVisitor import BKITVisitor
from BKITParser import BKITParser
from AST import *
from functools import reduce
class ASTGeneration(BKITVisitor):
    def visitProgram(self,ctx:BKITParser.ProgramContext):
        return Program(self.visitVardecl(ctx.var_declare()))

    def visitVardecl(self,ctx:BKITParser.Var_declareContext):
        return self.visitVariable_list(ctx.variable_list())
        
    def visitVariable_list(self,ctx:BKITParser.Variable_listContext):
        var = self.visit(ctx.variable())
        if isinstance(var,list):
            #Composite type
            iden = var[0][0]
            dimen = var[0][1]
            if ctx.initial_values():
                varInit = self.visitInitial_values(ctx.initial_values())
                lst= [VarDecl(iden,dimen,varInit)]
            else:
                lst= [VarDecl(iden,dimen,None)]
        else:
            if ctx.initial_values():
                varInit = self.visitInitial_values(ctx.initial_values())
                lst= [VarDecl(var,[],varInit)]
            else:
                lst= [VarDecl(var,[],None)]
        return lst + self.visitVariable_list(ctx.variable_list()) if ctx.variable_list() else  lst


    def visitVariable(self,ctx:BKITParser.VariableContext):
        return self.visitScalar_types(ctx.scalar_types()) if ctx.scalar_types() else self.visitComposite_types(ctx.Composite_types())

    def visitScalar_types(self,ctx:BKITParser.Scalar_typesContext):
        return Id(ctx.ID().getText())

    def visitComposite_types(self,ctx:BKITParser.Composite_typesContext):
        dimen = ctx.dimension()
        lst = reduce(lambda x,y: x+[self.visitDimension(y)],dimen,[])
        return [(Id(ctx.ID().getText()),lst)]

    def visitDimension(self,ctx:BKITParser.DimensionContext):
        return eval(ctx.IntegerLiteral().getText())

    def visitInitial_values(self,ctx:BKITParser.Initial_valuesContext):
        return None
    
    def visitFunc_declare(self,ctx:BKITParser.Func_declareContext):
        return None

    def visitFunc_head(self,ctx:BKITParser.Func_headContext):
        return None

    def visitParameter(self,ctx:BKITParser.ParameterContext):
        return None

    def visitParameter_list(self,ctx:BKITParser.Parameter_listContext):
        return None

    def visitFunc_body(self,ctx:BKITParser.Func_bodyContext):
        return None

    def visitStmt(self,ctx:BKITParser.StmtContext):
        return None

    def visitAssign_stmt(self,ctx:BKITParser.Assign_stmtContext):
        if ctx.scalar_types():
            return Assign(self.visitScalar_types(ctx.scalar_types()),self.visitExpr(ctx.Expr()))
        #Composite type TODO
    def visitIf_stmt(self,ctx:BKITParser.If_stmtContext):
        return None

    def visitFor_stmt(self,ctx:BKITParser.For_stmtContext):
        return None

    def visitWhile_stmt(self,ctx:BKITParser.While_stmtContext):
        return None

    def visitDo_while_stmt(self,ctx:BKITParser.Do_while_stmtContext):
        return None

    def visitBreak_stmt(self,ctx:BKITParser.Break_stmtContext):
        return Break()

    def visitContinue_stmt(self,ctx:BKITParser.Continue_stmtContext):
        return Contine()

    def visitCall_stmt(self,ctx:BKITParser.Call_stmtContext):
        return CallStmt(Id(ctx.ID().getText()),self.visitExpr_List(ctx.expr_List())) if ctx.expr_List() else CallStmt(Id(ctx.ID().getText()),[])

    def visitReturn_stmt(self,ctx:BKITParser.Return_stmtContext):
        return Break(ctx.expr()) if ctx.expr() else Break(None)

    def visitElement_expr(self,ctx:BKITParser.Element_exprContext):
        return None

    def visitExpr_index(self,ctx:BKITParser.Expr_indexContext):
        return None

    def visitIndexoperators(self,ctx:BKITParser.IndexoperatorsContext):
        return None

    def visitFunc_call(self,ctx:BKITParser.Func_callContext):
        return CallExpr(Id(ctx.ID().getText()),self.visitExpr_List(ctx.expr_List())) if ctx.expr_List() else CallStmt(Id(ctx.ID().getText()),[])

    def visitExpr(self,ctx:BKITParser.ExprContext):
        if ctx.getChildCount()==1:
            return self.visitExpr1(ctx.getChild(0))
        else:
            return BinaryOp(self.visitRelationaloperators(ctx.getChild(1)),self.visitExpr1(ctx.expr(0)),self.visitExpr1(ctx.expr(1)))

    def visitExpr1(self,ctx:BKITParser.Expr1Context):
        if ctx.getChildCount()==1:
            return self.visitExpr2(ctx.getChild(0))
        else:
            return BinaryOp(self.visitLogicaloperators(ctx.getChild(1)),self.visitExpr1(ctx.getChild(0)),self.visitExpr2(ctx.getChild(2)))

    def visitExpr2(self,ctx:BKITParser.Expr2Context):
        if ctx.getChildCount()==1:
            return self.visitExpr3(ctx.getChild(0))
        else:
            return BinaryOp(self.visitAddingoperators(ctx.getChild(1)),self.visitExpr2(ctx.getChild(0)),self.visitExpr3(ctx.getChild(2)))

    def visitExpr3(self,ctx:BKITParser.Expr3Context):
        if ctx.getChildCount()==1:
            return self.visitExpr4(ctx.getChild(0))
        else:
            return BinaryOp(self.visitMultiplyingoperators(ctx.getChild(1)),self.visitExpr3(ctx.getChild(0)),self.visitExpr4(ctx.getChild(2)))

    def visitExpr4(self,ctx:BKITParser.Expr4Context):
        if ctx.getChildCount()==1:
            return self.visitExpr5(ctx.getChild(0))
        else:
            return UnaryOp(self.visitNotoperator(ctx.getChild(0)),self.visitExpr4(ctx.getChild(1)))

    def visitExpr5(self,ctx:BKITParser.Expr5Context):
        if ctx.getChildCount()==1:
            return self.visitExpr6(ctx.getChild(0))
        else:
            return UnaryOp(self.visitSignoperators(ctx.getChild(0)),self.visitExpr5(ctx.getChild(1)))

    def visitExpr6(self,ctx:BKITParser.Expr6Context):
        if ctx.getChildCount()==1:
            return self.visitExpr7(ctx.getChild(0))
        else:
            return UnaryOp(self.visitIndexoperators(ctx.getChild(1)),self.visitExpr6(ctx.getChild(0)))
    def visitExpr7(self,ctx:BKITParser.Expr7Context):
        if ctx.operands():
            return self.visitOperands(ctx.operands())
        elif ctx.expr():
            return self.visitExpr(ctx.expr())
        else:
            return self.visitFunc_call(ctx.func_call())

    def visitOperands(self,ctx:BKITParser.OperandsContext):
        return Id(ctx.ID().getText) if ctx.ID() else self.visitLiteral(ctx.literal())

    def visitExpr_List(self,ctx:BKITParser.Expr_ListContext):
        if ctx.getChildCount()==1:
            return [self.visitExpr(ctx.expr(0))]
        else:
            return reduce(lambda x,y: x+ [self.visitExpr(y)],ctx.expr(),[])

    def visitNotoperator(self,ctx:BKITParser.NotoperatorContext):
        return ctx.getChild(0).getText()

    def visitSignoperators(self,ctx:BKITParser.SignoperatorsContext):
        return ctx.getChild(0).getText()

    def visitMultiplyingoperators(self,ctx:BKITParser.MultiplyingoperatorsContext):
        return ctx.getChild(0).getText()

    def visitAddingoperators(self,ctx:BKITParser.AddingoperatorsContext):
        return ctx.getChild(0).getText()

    def visitLogicaloperators(self,ctx:BKITParser.LogicaloperatorsContext):
        return ctx.getChild(0).getText()

    def visitRelationaloperators(self,ctx:BKITParser.RelationaloperatorsContext):
        return ctx.getChild(0).getText()

    def visitLiteral(self,ctx:BKITParser.LiteralContext):
        if ctx.IntegerLiteral():
            return IntLiteral(int(ctx.IntegerLiteral().getText()))
        elif ctx.FloatLiteral():
            return FloatLiteral(float(ctx.FloatLiteral().getText()))
        elif ctx.StringLiteral():
            return StringLiteral(ctx.StringLiteral().getText())
        elif ctx.booleanLiteral():
            return self.visitBooleanLiteral(ctx.booleanLiteral())
        else:
            return self.visitArrayLiteral(ctx.arrayLiteral())
    def visitBooleanLiteral(self,ctx:BKITParser.BooleanLiteralContext):
        return BooleanLiteral(bool(ctx.TRUE().getText())) if ctx.TRUE() else BooleanLiteral(bool(ctx.FALSE().getText()))

    def visitArrayLiteral(self,ctx:BKITParser.ArrayLiteralContext):
        return ArrayLiteral(self.visitArrayList(ctx.arrayList())) if ctx.arrayList() else ArrayLiteral([])
    
    def visitArrayList(self,ctx:BKITParser.ArrayListContext):
        if ctx.getChildCount()==1:
            return [self.visitLiteral(ctx.literal(0))]
        else:
            return reduce(lambda x,y: x+ [self.visitLiteral(y)],ctx.literal(),[])

    # def visit(self,ctx:BKITParser.ProgramContext):
    #     return None

