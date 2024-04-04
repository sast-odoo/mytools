## how to use
- clone the repo into your odoo directory
- start odoo shell (`python odoo-bin shell ...`)
- run `from mytools import *`

`def display(env, record, id=None, ttype=False, hide_empty=False, archived=False)`
Print fields of a record and their values with some other useful info

- `env` - the `odoo.api.Environment` (just pass the `env` that you're given when you start the shell)
- `record` - record, recordset, or `string` of a model name
- `id` - (optional) if `record` is passed a model name, then this is an `int` of the ID of the record to look up on that model. If `record` is passed as a model name and no `id` is supplied, `display` will use the fields of the first record returned by a `search([])` on that model
- `ttype` - (optional) a `string` giving a field ttype (i.e. `many2many`, `boolean`, `integer`) to filter results to fields of that type only
- `hide_empty` - (optional, default `False`) whether to display unset fields
- `archived` - (optional, default `False`) whether to display archived records

`def required(env, modelname)`
List the required fields on the given modelname

- `env` - the `odoo.api.Environment`
- `modelname` - `string` of model name (i.e. `'sale.order'`)

`def relations(env, modelname)`
List the relational (one2many, many2one, and many2many) fields on the given modelname, with what models they point to
(sort of a shorthand for calling `display` with `ttype` of one2many, many2many, and many2one)

- `env` - the `odoo.api.Environment`
- `modelname` - `string` of model name (i.e. `'sale.order'`)

`def fieldinfo(env, modelname, fieldname)`
List some useful information about a field, like its id, description, ttype, modules, whether its required or computed, and if its a relation some info on its relation

- `env` - the `odoo.api.Environment`
- `modelname` - `string` of model name (i.e. `'sale.order'`)
- `fieldname` - `string` of a field name (i.e. `'order_id`), can also be a dot-seperated path of related fields, like `'invoice_ids.invoice_line_ids.product_id.taxes_id'`, fieldinfo will traverse the path

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

# only print fields that are many2one
display(env, 'product.template', ttype='many2one')

# only print fields that are either char or boolean
display(env, 'product.template', ttype=('char','boolean'))

required(env, 'sale.order')

relations(env, 'res.partner')

fieldinfo(env, 'sale.order', 'order_line')

fieldinfo(env, 'sale.order', 'invoice_ids.invoice_line_ids.product_id.taxes_id')

```
