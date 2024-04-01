Display fields of a record with useful info like its ttype, relation, and inverse

## how to use
- clone the repo into your odoo directory
- start odoo shell (`python odoo-bin shell ...`)
- run `from mytools import *`

`def display(env, record, id=None, ttype=False, hide_empty=False, archived=False)`
## Parameters
- `env` - `odoo.api.Environment` object
- `record` - record, recordset, or `string` of a model name
- `id` - (optional) if `record` is passed a model name, then this is an `int` of the ID of the record to look up on that model. If `record` is passed as a model name and no `id` is supplied, `display` will use the fields of the first record returned by a `search([])` on that model
- `ttype` - (optional) a `string` giving a field ttype (i.e. `many2many`, `boolean`, `integer`) to filter results to fields of that type only
- `hide_empty` - (optional, default `False`) whether to display unset fields
- `archived` - (optional, default `False`) whether to display archived records

## examples
```
# print fields of a random record of 'product.template' model
display(env, 'product.template')

# print fields of the product.template with id 1
display(env, 'product.template', 1)

# print fields of a record object
record = env['product.template'].browse(1) # acquire some record
display(env, record)

# print fields of all records in a recordset
recordset = env['product.template'].browse([1,2,3]) # acquire some recordset
display(env, recordset)

# print fields of the product.template records with ids 1, 2, and 3
display(env, 'product.template', [1,2,3])

# print field data only, no values
# (display will print field data only if no record is given/found, and -1 is not a valid id for any record)
display(env, 'product.template', -1)
```
