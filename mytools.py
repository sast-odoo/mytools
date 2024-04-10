def views(env, modelname):
    ''' Print all views with this model '''
    base_views = env['ir.ui.view'].search([('model','=ilike',modelname),('inherit_id','in',(False, None))])
    inherit_views = env['ir.ui.view'].search([('model','=ilike',modelname),('inherit_id','not in',(False, None))])

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

def comodel_for(env, modelname):
    ''' find all fields that have this model as its relational comodel '''
    print(f"Fields that model '{modelname}' is a comodel for:")
    fields = env['ir.model.fields'].search([('relation','=ilike',modelname)])
    for field in sorted(fields, key=lambda f: f.model): #sort by model name
        print(f"{field.id}\t{field.model}: {field.name} ({field.ttype}, {inverse_str(env,field)})")

def required(env, modelname):
    ''' Print names of required fields on this model '''
    print(f"Required fields for model '{modelname}':")
    fields = env['ir.model.fields'].search([('model','=ilike',modelname), ('required','=',True)])
    for field in sorted(fields, key=lambda f: f.model):
        print(f"{field.id}\t{field.name} ({ttype_str(env, field.read()[0])})")

def data(env, record):
    ''' Return ir.model.data object associated with the record (if any) '''
    return(env['ir.model.data'].search([('model','=ilike',record._name),('res_id','=',record.id)]))

def unref(env, record):
    ''' Inverse of 'ref' method - finds a record's xml id from its record object '''
    return ", ".join(data(env, record).mapped('complete_name'))

def relations(env, modelname):
    ''' Print names of relational fields on this model '''
    print(f"Relational fields for model '{modelname}':")
    fields = env['ir.model.fields'].search([('model','=ilike',modelname), ('ttype','in',('many2one','many2many','one2many'))])
    for field in sorted(fields, key=lambda f: f.model):
        print(f"{field.id}\t{field.name} ({ttype_str(env, field.read()[0])})")

def get_inverse(env, field):
    ''' Find the inverse field on the related model of this relational field '''
    if field["ttype"] == "many2many":
        # many2many's don't use the inverse field, instead they link to other many2many's with a table, so find the other m2m field using this table
        if field['relation_table']:
            return env['ir.model.fields'].search([('relation_table','=ilike',field['relation_table']),('name','not ilike',field['name'])]).name
        return None

    if field['relation_field']:
        return field['relation_field']

    # if this field doesn't have the inverse set, the inverse field still may have ITS inverse set as this field
    field_result = env['ir.model.fields'].search([('relation','=ilike', field['model']), ('relation_field','=ilike',field['name'])])
    if len(field_result)>1:
        return ", ".join(field_result.mapped("name"))
    if len(field_result)==1:
        return field_result.name
    return None

def inverse_str(env, field):
    ''' return print-ready string result of get_inverse '''
    inv = get_inverse(env, field)
    if inv:
        return f"inverse to {inv}"
    return "no inverse"

def ttype_str(env, field):
    ''' return print-ready string representing the ttype (and relational data) '''
    retval = field['ttype']
    if field['ttype'] in ('many2one','many2many','one2many'):
        retval += f" to {field['relation']}, {inverse_str(env, field)}"
    return retval

def val_str(field, val, print_vals):
    ''' return print-ready string representing the value '''
    if not print_vals:
        #return ""
        return f" - {field['field_description']}"
    if field['ttype']=='binary' and val:
        return ": [binary data]"
    return f": {val}"

def fieldinfo(env, modelname, fieldname=""):

    if isinstance(modelname, int):
        field = env['ir.model.fields'].browse(modelname)
        modelname = field.model
        fieldname = field.name

    else:
        if "." in fieldname:
            split_fields = fieldname.split(".")
            joined_fields = ".".join(split_fields[1:])

            this_field = env['ir.model.fields'].search([('model','=ilike',modelname),('name','=ilike',split_fields[0])]).read()[0]
            related_model = this_field['relation']
            print(f"* {this_field['name']} ({this_field['ttype']}) --> {this_field['relation']}")

            fieldinfo(env, related_model, joined_fields)
            return

        field = env['ir.model.fields'].search([('model','=ilike',modelname),('name','=ilike',fieldname)]).read()[0]

    print_list = [
        f"===== {modelname} - {fieldname} ({field['ttype']}) =====",
        f"Field ID: {field['id']}",
        f"Description: {field['field_description']}",
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
            f"\tInverse field: {get_inverse(env, field)}",
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

        selections = env['ir.model.fields.selection'].browse(field['selection_ids'].ids)
        #print(selections)
        for selection in selections:
            print_list.append(f'\t{selection.id}: {selection.value} - "{selection.name}"')

    for print_item in print_list:
        print(print_item)

def display(env, record, id=None, ttype=False, hide_empty=False, archived=False):
    if isinstance(record,str):
        model_name = record

        if not id:
            display(env,
                    env[model_name].search([],limit=1),
                    ttype=ttype,
                    hide_empty=hide_empty,
                    archived=archived)
            return
        
        if isinstance(id,int):
            search_domain = [("id","=",id)]

        elif isinstance(id,(list,tuple)):
            search_domain = [("id","in",id)]

        else:
            raise TypeError("param 'id' should be an int or a list of int")
        
        result = env[model_name].search(search_domain)

        if ("active" in result._fields) and (not result or archived):
            search_domain.append(("active","in",(True,False)))

        result = env[model_name].search(search_domain)
        display(env, result, ttype=ttype, hide_empty=hide_empty)

        return

    domain = [('model','=ilike',record._name)] # _name attribute of a record gets its model name

    if ttype:
        if isinstance(ttype,str):
            domain.append(('ttype','=ilike',ttype))
        elif isinstance(ttype,(list,tuple)):
            domain.append(('ttype','in',ttype))

    read_fields = env['ir.model.fields'].search(domain).read()
    
    fields_dict = {}
    for field in read_fields:
        fields_dict[field['name']] = field
        
    print_values = True
    
    if len(record)==0:
        print("No records, printing field data only")
        print_values = False

    if len(record)<=1:
        archived_str = ""
        id_str = ", id: %d " % record.id
        if not print_values:
            id_str = " [FIELDS ONLY]"
        elif "active" in record and not record.active:
            archived_str = " [ARCHIVED]"
        
        print('===== %s%s%s =====' % (record._name, id_str, archived_str))

        record_name_field = record._rec_name # find what field this model uses as its name

        if print_values:
            print(f"* Record name ({record_name_field}): '{record[record_name_field]}'")
            unref_name = unref(env, record)
            if unref_name:
                print(f"* xml_id: {unref_name}")
                print(f"* ir.model.data id: {', '.join(str(i) for i in data(env, record).ids)}")
        else:
            print(f"* Record name field: {record_name_field}")

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

            print(f"{fields_dict[key]['id']}\t{key} ({ttype_str(env, fields_dict[key])}){val_str(fields_dict[key], val, print_values)}")
            
    else:
        for rec in sorted(record, key=lambda i: i.id):
            display(env, rec, ttype=ttype, hide_empty=hide_empty, archived=archived)
            print("\n")
