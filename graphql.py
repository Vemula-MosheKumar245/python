from fastapi import FastAPI
from starlette.graphql import GraphQLApp
import graphene

class Calculator(graphene.ObjectType):
    concat = graphene.String()
    add = graphene.String()

    def resolve_concat(self, info):
        return "this is concatenation"

    def resolve_add(self, info):
        return "this is addition"

app = FastAPI()
app.add_route("/", GraphQLApp(schema=graphene.Schema(query=Calculator)))
