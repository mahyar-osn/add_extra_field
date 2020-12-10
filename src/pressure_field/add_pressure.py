import os
import argparse

from opencmiss.zinc.context import Context
from opencmiss.zinc.field import Field
from opencmiss.utils.zinc.field import create_field_finite_element
from opencmiss.utils.zinc.general import ChangeManager


class ProgramArguments(object):
    pass


def add_field(field_module, field_name, field_value):
    with ChangeManager(field_module):
        field_cache = field_module.createFieldcache()

        node_set = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        node_template = node_set.createNodetemplate()
        field = field_module.findFieldByName(field_name)
        node_template.defineField(field)

        node_iter = node_set.createNodeiterator()
        node = node_iter.next()
        while node.isValid():
            field_cache.setNode(node)
            node.merge(node_template)
            if isinstance(field_value, ("".__class__, u"".__class__)):
                field.assignString(field_cache, field_value)
            elif isinstance(field_value, list):
                field.assignReal(field_cache, field_value)
            node = node_iter.next()

        # merge
        mesh = field_module.findMeshByDimension(2)
        element_template = mesh.createElementtemplate()
        field = field_module.findFieldByName(field_name)
        element_template.defineFieldElementConstant(field, -1)

        element_iter = mesh.createElementiterator()
        element = element_iter.next()
        while element.isValid():
            result = element.merge(element_template)
            print('Element ', element.getIdentifier(), 'merge', result)
            field_cache.setElement(element)
            if isinstance(field_value, list):
                field.assignReal(field_cache, field_value)
            element = element_iter.next()


class AddExtraField(object):

    def __init__(self, filename, field_info, output_filename):
        self._context = Context("AddField")
        self._region = self._context.getDefaultRegion()
        self._region.readFile(filename)

        self._output_file = output_filename

        self._add_field(field_info)

    def _get_mesh(self):
        fm = self._region.getFieldmodule()
        for dimension in range(3, 0, -1):
            mesh = fm.findMeshByDimension(dimension)
            if mesh.getSize() > 0:
                return mesh
        raise ValueError('Model contains no mesh')

    def _add_field(self, field_info):
        fm = self._region.getFieldmodule()

        for field_name in field_info:
            create_field_finite_element(fm, field_name, 1, type_coordinate=False)
            field_value = field_info[field_name]
            add_field(fm, field_name, field_value)

        self._write()

    def _write(self):
        self._region.writeFile(self._output_file)


def main():
    args = parse_args()
    if os.path.exists(args.input_ex):
        if args.output_ex is None:
            filename = os.path.basename(args.input_ex)
            dirname = os.path.dirname(args.input_ex)
            output_ex = os.path.join(dirname, filename.split('.')[0] + '_extra_field.' + filename.split('.')[1])
        else:
            output_ex = args.output_ex

    teg = AddExtraField(args.input_ex, {'pressure': [1000.0]}, output_ex)
    # teg.add_field()


def parse_args():
    parser = argparse.ArgumentParser(description="Add an extra field to an existing EX mesh file.")
    parser.add_argument("input_ex", help="Location of the input EX file.")
    parser.add_argument("-o", "--output-ex", help="Location of the output ex file. "
                                                  "[defaults to the location of the input file if not set.]")

    program_arguments = ProgramArguments()
    parser.parse_args(namespace=program_arguments)

    return program_arguments


if __name__ == "__main__":
    main()
