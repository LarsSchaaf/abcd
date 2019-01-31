# from database import init_db
# from flask import Flask
# from flask_graphql import GraphQLView
# from app.schema import schema
#
# default_query = '''
# {
#   allEmployees {
#     edges {
#       node {
#         id,
#         name,
#         department {
#           id,
#           name
#         },
#         roles {
#           edges {
#             node {
#               id,
#               name
#             }
#           }
#         },
#         leader {
#           id,
#           name
#         }
#         tasks {
#           edges {
#             node {
#               name,
#               deadline
#             }
#           }
#         }
#       }
#     }
#   }
# }'''.strip()
#
# app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))
