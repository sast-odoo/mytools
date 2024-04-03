def required(env, modelname):
    print(f"Required fields for model '{modelname}':")
    fields = env['ir.model.fields'].search([('model','=ilike',modelname), ('required','=',True)])
    for field in fields:
        print(f"\t{field.name} ({field.ttype})")

def relations(env, modelname):
    print(f"Relational fields for model '{modelname}':")
    fields = env['ir.model.fields'].search([('model','=ilike',modelname), ('ttype','in',('many2one','many2many','one2many'))])
    for field in fields:
        print(f"\t{field.name} ({field.ttype} to {field.relation})")

def fieldinfo(env, modelname, fieldname):
    #print(modelname,fieldname)

    if "." in fieldname:
        #print("chained fieldname passed")
        split_fields = fieldname.split(".")
        joined_fields = ".".join(split_fields[1:])

        this_field = env['ir.model.fields'].search([('model','=ilike',modelname),('name','=ilike',split_fields[0])]).read()[0]
        related_model = this_field['relation']
        print(f"* {this_field['name']} ({this_field['ttype']}) --> {this_field['relation']}")

        fieldinfo(env, related_model, joined_fields)
        return

    field = env['ir.model.fields'].search([('model','=ilike',modelname),('name','=ilike',fieldname)]).read()[0]
    #print(field)

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

        selections = env['ir.model.fields.selection'].browse(field['selection_ids'])
        for selection in selections:
            print_list.append(f'\t{selection.id}: {selection.value} - "{selection.name}"')

    for print_item in print_list:
        print(print_item)


def get_inverse(env, field):
    #print(field)
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

def display(env, record, id=None, ttype=False, hide_empty=False, archived=False, print_header=True):
    if isinstance(record,str):
        if not id:
            if archived:
                display(env,
                        env[record].search([("active","in",(True,False))],limit=1),
                        ttype=ttype,
                        hide_empty=hide_empty,
                        print_header=print_header)
            else:
                display(env,
                        env[record].search([],limit=1),
                        ttype=ttype,
                        hide_empty=hide_empty,
                        print_header=print_header)
            return
        
        if isinstance(id,int):
            search_domain = [("id","=",id)]

        elif isinstance(id,(list,tuple)):
            search_domain = [("id","in",id)]

        else:
            raise TypeError("param 'id' should be an int or a list of int")
        result = env[record].search(search_domain)
        if not result or archived:
            search_domain.append(("active","in",(True,False)))

        result=env[record].search(search_domain)
        display(env, result, ttype=ttype, hide_empty=hide_empty, print_header=print_header)

        return

    if ttype:
        read_fields = env['ir.model.fields'].search([('model','=ilike',record._name),('ttype','=like',ttype)]).read()
    else:
        read_fields = env['ir.model.fields'].search([('model','=ilike',record._name)]).read()
    
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
        
        if print_header:
            print('\n===== %s%s%s =====' % (record._name, id_str, archived_str))

        if print_values:
            sorted_items = sorted(list(record.read()[0].items()), key=lambda i: i[0])
        else:
            sorted_items = sorted(list(fields_dict.items()), key=lambda i: i[0])

        for key,val in sorted_items:
            if hide_empty and not val:
                continue
            try: # fake fields like 'in_group_11' will throw keyerror
                ttype = fields_dict[key]['ttype']
            except KeyError:
                continue

            print(key, "(%s" % ttype, end="")

            if ttype in ("many2one","one2many","many2many"):

                inverse_name = get_inverse(env, fields_dict[key])

                if inverse_name:
                    inverse_string = 'inverse to %s' % inverse_name
                else:
                    inverse_string = 'no inverse'

                print(" to %s, %s)" % (fields_dict[key]['relation'], inverse_string), end="")
            else:
                print(")", end="")
            
            if print_values:
                print(": ",end="")
                if ttype=="binary":
                    if val:
                        print("[binary data]")
                    else:
                        print(val)
                else:
                    print(val)
            else:
                print()

    else:
        for rec in sorted(record, key=lambda i: i.id):
            display(env, rec, ttype=ttype, hide_empty=hide_empty, archived=archived, print_header=print_header)
