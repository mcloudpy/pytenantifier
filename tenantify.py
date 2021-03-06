#!/usr/bin/python
# -*- coding: utf8 -*-

import argparse
import re
import sys


parser = argparse.ArgumentParser(description='Tenantify the SQLAlchemy models file')

parser.add_argument('models_file', type=argparse.FileType('r'),
                   help='File that contains the SQLAlchemy model classes (generally called models.py)')

parser.add_argument('-o', type=argparse.FileType('w'), default=sys.stdout, dest="outfile",
                    help="File to which the modified models.py file will be written")

parser.add_argument('-b', '--baseclass', default="Base", dest="baseclass",
                    help="The name of the base class that is being used to describe the model, as it appers in the source code (Default: Base)")

args = parser.parse_args()



# TODO: Limitation: Guess the indent to use. Respect that indent when code-generating.
# TODO: Detect Base name automatically.

TENANTS_TABLE_CODE = """

from sqlalchemy import Column, Integer, Unicode, ForeignKey



class Tenant(%s):
    '''
        AUTOGENERATED
        Table to store the tenants.
    '''

    __tablename__ = 'Tenant'
    id = Column('id', Integer, primary_key=True)
    name = Unicode(50)

    def __init__(self, name=None):
        super(Tenant, self).__init__()
        self.name = name

class TenantedBase(%s):
    '''
        AUTOGENERATED
        Table for all tables which should reference a tenant to inherit from.
    '''
    tenant_id = Column('tenant_id', Integer, ForeignKey('Tenant.id'))



""" % (args.baseclass, args.baseclass)

REG_IDENTIFIER = r"[a-zA-Z_][a-zA-Z0-9_]*"
REG_CLASS_DEF = r"class\s*(" + REG_IDENTIFIER + r")\(%s" % re.escape(args.baseclass)



models = args.models_file.read()


# Inherit from TenantBase rather than Base
def replacer(m):
    if m.groups(1) not in ('AlembicVersion',):
        rep = m.expand(r'class \1(TenantedBase')
        print "Replacing class %s with %s" % (m.groups(1), rep)
        return rep
    return m.expand(r'\g<0>')

models_with_classes = re.sub(REG_CLASS_DEF, replacer, models, re.MULTILINE | re.DOTALL)


print "Adding header with TenantedBase and imports"

# Insert our magic header at an appropriate point (before the first class declaration)
insertion_point = re.search(r'^class\s', models_with_classes, re.MULTILINE | re.DOTALL)

models_with_header = models_with_classes[:insertion_point.start()] + TENANTS_TABLE_CODE + models_with_classes[insertion_point.start():]

print "Writing to the output file"

args.outfile.write(models_with_header)
