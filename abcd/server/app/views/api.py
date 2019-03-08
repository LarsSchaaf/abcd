from flask import Blueprint
from flask_graphql import GraphQLView

# from app_old.models import Atoms
from abcd.server.app import schema

bp = Blueprint('api', __name__)

bp.add_url_rule('graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))


def fix_id(calc):
    calc['_id'] = str(calc['_id'])
    return calc


# def make_hash(o):
#     """
#     Makes a hash from a dictionary, list, tuple or set to any level, that contains
#     only other hashable types (including any lists, tuples, sets, and
#     dictionaries).
#     """
#
#     if isinstance(o, (set, tuple, list)):
#
#         return tuple([make_hash(e) for e in o])
#
#     elif not isinstance(o, dict):
#
#         return hash(o)
#
#     new_o = copy.deepcopy(o)
#     for k, v in new_o.items():
#         new_o[k] = make_hash(v)
#
#     return hash(tuple(frozenset(sorted(new_o.items()))))
#
#
# class QueryString(object):
#     def __init__(self, query: str):
#         self.query = query
#
#     def parse(self):
#         raise NotImplementedError
#
#
# # endpoint to create new user
# @bp.route("/calculation", methods=["POST"])
# def query_calculation():
#     response = {
#         'query': request.json,
#         'results': []
#     }
#     return jsonify(response)
#
#
# # endpoint to show all users
# @bp.route("/calculation", methods=["GET"])
# def get_calculation():
#     all_calculations = [str(calculation['id']) for calculation in Atoms.objects]
#
#     return jsonify(all_calculations)
#
#
# # endpoint to get user detail by id
# @bp.route("/calculation/<calc_id>", methods=["GET"])
# def calculation_detail(calc_id):
#     calculation = Atoms.objects.get_or_404(id=calc_id)
#     return jsonify(calculation)
#
#
# @bp.route("/calculation", methods=["PUT"])
# def add_calculation():
#     atoms = Atoms(**request.json).save()
#     return jsonify(str(atoms.id))
#
#
# # endpoint to delete user
# @bp.route("/calculation/<calc_id>", methods=["DELETE"])
# def delete_calculation(calc_id):
#     calculation = Atoms.objects.get_or_404(id=calc_id)
#     calculation.delete()
#     return jsonify(str(calculation.id))