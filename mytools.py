try:
    from thefuzz import fuzz
    fuzz_imported = True
except ImportError:
    fuzz_imported = False

# TODO - ability to display all records of a relationship field
# like if a record has a field named 'related_ids' with [1,2,3,4,5],
# some way to just type record.related_ids and display all of [1,2,3,4,5]

# TODO - viewing computed fields in fieldinfo doens't behave as expected

# TODO - make display() show what fields are computed (like how it does for related)

# TODO - referencing() but get it to return recordsets
# i.e. referencing(record, model='res.partner') returns a recordset of res.partner records that reference this record
# bonus: referencing(record, model=['res.partner','sale.order']) return a list of [res.partner(...), sale.order(...)] list of recordsets
# or {'res.partner': res.partner(...), 'sale.order': sale.order(...)}

class Tool():
    def __init__(self, env):
        self.env = env

        self.model_names = env['ir.model'].search([]).mapped('model')

    def get(self, modelname, id):
        if not self.is_valid_modelname(modelname):
            return
        return self.env[modelname].browse(id)

    def referencing(self, record):
        result = self._comodel_for(record._name)
        for field_id, model, name, ttype, inverse in result:
            field = self.env["ir.model.fields"].browse(field_id)
            if field.store: # can't search non stored fields
                recs = self.env[model].search([(name, '=', record.id)])
                if recs:
                    print(f"{field_id}\t{model} - on {name} ({ttype}, {self.inverse_str(None, inverse=inverse)}):", end=" ")
                    if len(recs) > 30:
                        print(f"[{len(recs)} records]")
                    else:
                        print(*recs.ids, sep=", ")

    def is_valid_modelname(self, string):
        if string in self.model_names:
            return True
        if fuzz_imported:
            print(f"No model named '{string}', did you mean:")
            for match in sorted(self.model_names, key=lambda i: fuzz.ratio(i, string), reverse=True)[:4]:
                print(f"\t{match}")
        else:
            print(f"No model named '{string}' in database.")
        return False
    
    def views(self, modelname):
        ''' Print all views with this model '''
        if not self.is_valid_modelname(modelname):
            return

        base_views = self.env['ir.ui.view'].search([('model','=ilike',modelname),('inherit_id','in',(False, None))])
        inherit_views = self.env['ir.ui.view'].search([('model','=ilike',modelname),('inherit_id','not in',(False, None))])

        base_dict = {}
        for filename in set(base_views.mapped("arch_fs")):
            base_dict[filename] = base_views.search([('arch_fs','=ilike',filename)])

        inherit_dict = {}
        for filename in set(inherit_views.mapped("arch_fs")):
            inherit_dict[filename] = inherit_views.search([('arch_fs','=ilike',filename)])

        print("Base views:")
        for filename,view_records in sorted(base_dict.items(),key=lambda tup: tup[0]):
            print(f"\tIn file '{filename}':")
            for view in sorted(view_records,key=lambda v: v['type']):
                print(f"\t\t{view['type']}:\t{view['xml_id']} (id: {view['id']})")

        print("\nInheriting:")
        for filename,view_records in sorted(inherit_dict.items(),key=lambda tup: tup[0]):
            print(f"\tIn file '{filename}':")
            for view in sorted(view_records,key=lambda v: v['type']):
                print(f"\t\t{view['type']}:\t{view['xml_id']} (id: {view['id']})")

    def _comodel_for(self, modelname):
        fields = self.env['ir.model.fields'].search([('relation','=ilike',modelname)])
        result = []

        for field in sorted(fields, key=lambda f: f.model): #sort by model name
            result.append((field.id, field.model, field.name, field.ttype, self.get_inverse(field)))
        return result


    def comodel_for(self, modelname):
        ''' find all fields that have this model as its relational comodel 
        (user friendly wrapper for __comodel_for that prints the results) '''
        if not self.is_valid_modelname(modelname):
            return
        
        print(f"Fields that model '{modelname}' is a comodel for:")

        result = self._comodel_for(modelname)
        for id, model, name, ttype, inverse in result:
            print(f"{id}\t{model}: {name} ({ttype}, {self.inverse_str(None, inverse=inverse)})")


        #fields = self.env['ir.model.fields'].search([('relation','=ilike',modelname)])
        #for field in sorted(fields, key=lambda f: f.model): #sort by model name
        #    print(f"{field.id}\t{field.model}: {field.name} ({field.ttype}, {self.inverse_str(field)})")

    def required(self, modelname):
        ''' Print names of required fields on this model '''
        if not self.is_valid_modelname(modelname):
            return
    
        print(f"Required fields for model '{modelname}':")
        fields = self.env['ir.model.fields'].search([('model','=ilike',modelname), ('required','=',True)])
        for field in sorted(fields, key=lambda f: f.model):
            print(f"{field.id}\t{field.name} ({self.ttype_str(field.read()[0])})")

    def data(self, record):
        ''' Return ir.model.data object associated with the record (if any) '''
        return(self.env['ir.model.data'].search([('model','=ilike',record._name),('res_id','=',record.id)]))

    def unref(self, record):
        ''' Inverse of 'ref' method - finds a record's xml id from its record object '''
        return ", ".join(self.data(record).mapped('complete_name'))

    def relations(self, modelname):
        ''' Print names of relational fields on this model '''
        if not self.is_valid_modelname(modelname):
            return

        print(f"Relational fields for model '{modelname}':")
        fields = self.env['ir.model.fields'].search([('model','=ilike',modelname), ('ttype','in',('many2one','many2many','one2many'))])
        for field in sorted(fields, key=lambda f: f.model):
            print(f"{field.id}\t{field.name} ({self.ttype_str(field.read()[0])})")

    def get_inverse(self, field):
        ''' Find the inverse field on the related model of this relational field '''
        if field["ttype"] == "many2many":
            # many2many's don't use the inverse field, instead they link to other many2many's with a table, so find the other m2m field using this table
            if field['relation_table']:
                return ", ".join(self.env['ir.model.fields'].search([('relation_table','=ilike',field['relation_table']),('name','not ilike',field['name'])]).mapped('name'))
            return None

        if field['relation_field']:
            return field['relation_field']

        # if this field doesn't have the inverse set, the inverse field still may have ITS inverse set as this field
        field_result = self.env['ir.model.fields'].search([('relation','=ilike', field['model']), ('relation_field','=ilike',field['name'])])
        if len(field_result)>1:
            return field_result.mapped("name")
        if len(field_result)==1:
            return field_result.name
        return None

    def inverse_str(self, field, inverse=-1):
        ''' return print-ready string result of get_inverse '''
        if inverse != -1:
            inv = inverse
        else:
            inv = self.get_inverse(field)
        
        if inv:
            if isinstance(inv, list):
                inv = ", ".join(inv)
            return f"inverse to {inv}"
        return "no inverse"

    def ttype_str(self, field):
        ''' return print-ready string representing the ttype (and relational data) '''
        retval = ""

        retval = field['ttype']

        if field['ttype'] in ('many2one','many2many','one2many'):
            retval += f" to {field['relation']}"

        if field['related']:
            retval = "RELATED via " + field['related'] + " - " + retval
        elif field['ttype'] in ('many2one','many2many','one2many'):
            retval += f", {self.inverse_str(field)}"

        return retval

    def val_str(self, field, val, print_vals):
        ''' return print-ready string representing the value '''
        if not print_vals:
            #return ""
            return f" - {field['field_description']}"
        if field['ttype']=='binary' and val:
            return ": [binary data]"
        return f": {val}"

    def fieldinfo(self, modelname, fieldname=""):

        if isinstance(modelname, int):
            field_id = modelname
            field = self.env['ir.model.fields'].browse(field_id)
            modelname = field.model
            fieldname = field.name

        elif isinstance(modelname, (list,tuple)):
            if isinstance(modelname[0], int):
                id_list = modelname
                for id_num in id_list:
                    self.fieldinfo(id_num)
                return
                
        else:
            if not self.is_valid_modelname(modelname):
                return
            if "." in fieldname:
                split_fields = fieldname.split(".")
                joined_fields = ".".join(split_fields[1:])

                this_field = self.env['ir.model.fields'].search([('model','=ilike',modelname),('name','=ilike',split_fields[0])]).read()[0]
                related_model = this_field['relation']
                print(f"* {this_field['name']} ({this_field['ttype']}) --> {this_field['relation']}")

                self.fieldinfo(related_model, joined_fields)
                return

            field = self.env['ir.model.fields'].search([('model','=ilike',modelname),('name','=ilike',fieldname)]).read()[0]

        print_list = [
            f"===== {modelname} - {fieldname} ({field['ttype']}) =====",
            f"Field ID: {field['id']}",
            f"Description: {field['field_description']}",
        f"Related: {field['related']}",
        # TODO - if field is related, should print data of the related field
        f"Modules: {field['modules']}",
        f"Required: {field['required']}",
        f"Compute: {field['compute']}",
        f"Store: {field['store']}",
        ]

        if field['compute']:
            print_list.insert(6, f"Depends on: {field['depends']}")
        
        if field['relation']:
            print_list.extend([
                "*** Relation info ***",
                f"\tRelated model: {field['relation']}",
                f"\tInverse field: {self.get_inverse(field)}",
                f"\tOn delete: {field['on_delete']}",
            ])

            if field['ttype'] == 'many2many':
                print_list.extend([
                    f"\tM2M table: {field['relation_table']}",
                    f"\tColumn 1: {field['column1']}",
                    f"\tColumn 2: {field['column2']}",
                ])

        if field['ttype'] == 'selection':

            print_list.append("*** Selection info ***")

            if isinstance(field['selection_ids'],list):
                selections = self.env['ir.model.fields.selection'].browse(field['selection_ids'])
            else:
                selections = self.env['ir.model.fields.selection'].browse(field['selection_ids'].ids)

            #print(selections)
            for selection in selections:
                print_list.append(f'\t{selection.id}: {selection.value} - "{selection.name}"')

        for print_item in print_list:
            print(print_item)

    def display(self, record, id=None, fields=None, ttype=False, hide_empty=False, archived=False, toprint=True):
        print_list = []

        if isinstance(record,str):
            if not self.is_valid_modelname(record):
                return
            model_name = record

            if not id:
                self.display(
                        self.env[model_name].search([],limit=1),
                        fields=fields,
                        ttype=ttype,
                        hide_empty=hide_empty,
                        archived=archived,
                        toprint=toprint)
                return
            
            if isinstance(id,int):
                search_domain = [("id","=",id)]

            elif isinstance(id,(list,tuple)):
                search_domain = [("id","in",id)]

            else:
                raise TypeError("param 'id' should be an int or a list of int")
            
            result = self.env[model_name].search(search_domain)

            if ("active" in result._fields) and (not result or archived):
                search_domain.append(("active","in",(True,False)))

            result = self.env[model_name].search(search_domain)
            self.display(result, fields=fields, ttype=ttype, hide_empty=hide_empty, toprint=toprint)

            return

        domain = [('model','=ilike',record._name)] # _name attribute of a record gets its model name

        if ttype:
            if isinstance(ttype,str):
                domain.append(('ttype','=ilike',ttype))
            elif isinstance(ttype,(list,tuple)):
                domain.append(('ttype','in',ttype))

        if fields:
            if isinstance(fields,str):
                domain.append(('name','=ilike',fields))
            elif isinstance(fields,(list,tuple)):
                domain.append(('name','in',fields))

        read_fields = self.env['ir.model.fields'].search(domain).read()
        
        fields_dict = {}
        for field in read_fields:
            fields_dict[field['name']] = field
            
        print_values = True
        
        if len(record)==0:
            print_list.append("No records, printing field data only")
            print_values = False

        if len(record)<=1:
            archived_str = ""
            try:
                id_str = ", id: %d " % record.id
            except TypeError:
                id_str = ", id: " + str(record.id)
            if not print_values:
                id_str = " [FIELDS ONLY]"
            elif "active" in record and not record.active:
                archived_str = " [ARCHIVED]"
            
            print_list.append('===== %s%s%s =====' % (record._name, id_str, archived_str))

            record_name_field = record._rec_name # find what field this model uses as its name
            
            if print_values:
                if record_name_field:
                    print_list.append(f"* Record name ({record_name_field}): '{record[record_name_field]}'")
                else:
                    print_list.append("* No record name field on model")
                unref_name = self.unref(record)
                if unref_name:
                    print_list.append(f"* xml_id: {unref_name}")
                    print_list.append(f"* ir.model.data id: {', '.join(str(i) for i in self.data(record).ids)}")
            else:
                print_list.append(f"* Record name field: {record_name_field}")

            if print_values:
                sorted_items = sorted(list(record.read()[0].items()), key=lambda i: i[0])
            else:
                sorted_items = sorted(list(fields_dict.items()), key=lambda i: i[0])

            for key,val in sorted_items:
                if hide_empty and not val:
                    continue
                if key not in fields_dict or "ttype" not in fields_dict[key]:
                    # fake fields like 'in_group_11' will throw keyerror
                    continue

                print_list.append(f"{fields_dict[key]['id']}\t{key} ({self.ttype_str(fields_dict[key])}){self.val_str(fields_dict[key], val, print_values)}")
                
        else:
            for rec in sorted(record, key=lambda i: i.id):
                self.display(rec, fields=fields, ttype=ttype, hide_empty=hide_empty, archived=archived, toprint=toprint)
                print_list.append("\n")

        if toprint:
            for line in print_list:
                print(line)
        else:
            return print_list

    def display_proc(self, proc):
        print(f"""
~~~~~~ Procurement ~~~~~~
\tproduct_id: {proc.product_id.id}, "{proc.product_id.name}"
\tproduct_qty: {proc.product_qty}
\tproduct_uom: {proc.product_uom.id}, "{proc.product_uom.name}"
\tlocation_id: {proc.location_id.id}, "{proc.location_id.name}"
\tname: "{proc.name}"
\torigin: "{proc.origin}"
\tcompany_id: {proc.company_id.id}, "{proc.company_id.name}"
\tvalues:""")
        for key,value in proc.values.items():
            print(f"\t\t{key}: ",end="")
            try:
                print(f'{value}, "{value.name}"')
            except AttributeError:
                print(f"{value}")

    def hard_delete(self, record, id=None):
        if isinstance(record,str):
            if not self.is_valid_modelname(record):
                return
            model_name = record
            return self.hard_delete(self.get(model_name, id))
        if not record:
            print("No record given / no record with this id exists")
            return
        print(f"Deleting record with id {record.id} from table {record._table}")
        self.env.cr.execute(f"DELETE FROM {record._table} WHERE id={record.id}")
