Clone this repo in the inner odoo directory (i.e. so it's alongside of the directories cli, conf, tools etc)
You can import and use the tool in the odoo shell or in odoo modules to help debug, just import `from odoo.mytools import Tool` either in the shell or at the top of your module file. (just remember to remove all references to it before you push, if you're doing a dev)

To use the methods, you must create a "Tool" object, this object is instantiated with the odoo 'env' object, such as `t = Tool(env)`. All the methods can then be accessed by doing `t.display(...)`

In order to avoid having to type `from odoo.mytools import` and `t = Tool(env)` every single time you start the shell, you can modify the odoo/cli/shell.py file: add `from ..mytools import Tool` to the top of the file, then under the line `local_vars['self'] = env.user` in the shell() function, add the line `local_vars['t'] = Tool(env)`, now you can use `t` to access all the methods without having to instantiate it every time.

## Useful methods

### display(record OR str modelname, int id=None, ttype=False, hide_empty=False, archived=False)
- display all the fields and their values of the record along with a bunch of useful info about the record and fields. The number at the left of each field line is the ir.model.fields ID of that field (can be used in fieldinfo)
### views(str modelname)
- display all the views for that model in the database, noting the filepath of each view and whether or not it's inherited
### comodel_for(str modelname)
- Find and display all fields that have this model as its relational comodel
### required(str modelname)
- print names of required fields on this model
### unref(record)
- inverse of "ref" method - find a record's xml id from its record object, if it has one
### relations(str modelname)
- print names of all relational (many2one, x2many) fields on the model with useful info
### fieldinfo(str modelname OR int fieldId OR tuple (int fieldId))
- print useful info about a particular field
### referencing(record)
- display all records that point to this record on a relational field
### get(modelname, id)
- shortcut for `env[modelname].browse(id)`
