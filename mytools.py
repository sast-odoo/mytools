from odoo import api, fields, models

def display(env, record, id=None, ttype=False, hide_empty=False, archived=False):
    '''
    how to use:
        put mytools.py in your odoo directory
        start odoo shell (python odoo-bin shell...)
        run "from mytools import display"
    
    usage options:
        - display(env, record)
            where record is a record object ie. res.partner(1,) to print its fields
        - display(env, recordset)
            where recordset is a recordset object ie. res.partner(1,2,3,) to print all
        - display(env, modelname, id)
            where modelname is a string like "res.partner" and id is an int, to print the fields of the record with that id
        - display(env, modelname, ids)
            where modelname is a string and ids is a list or tuple of ints representing ids, to print all those records
        - display(env, modelname)
            print the fields of a random record on that model (the first record returned by search([]))
        pass True to hide_empty to skip printing unset fields
    '''

    #print("record:",record,"id:",id,"hide_empty:",hide_empty)
    if isinstance(record,str):
        if not id:
            print("Model name provided; printing sample record")
            if archived:
                display(env, env[record].search([("active","in",(True,False))],limit=1), ttype=ttype, hide_empty=hide_empty)
            else:
                display(env, env[record].search([],limit=1), ttype=ttype, hide_empty=hide_empty)
                
            return
        else:
            #print(id)
            
            if isinstance(id,int):
                #result = env[record].search([("id","=",id)])
                #display(env, env[record].search([("id","=",id)]), hide_empty=hide_empty)
                search_domain = [("id","=",id)]
            elif isinstance(id,(list,tuple)):
                #result = env[record].search([("id","in",id)])
                #display(env, env[record].search([("id","in",id)]), hide_empty=hide_empty)
                search_domain = [("id","in",id)]
            else:
                raise TypeError("param 'id' should be an int or a list of int")
            result = env[record].search(search_domain)
            if not result or archived:
                search_domain.append(("active","in",(True,False)))
            result=env[record].search(search_domain)
            display(env, result, ttype=ttype, hide_empty=hide_empty)
            return

    if ttype:
        read_fields = env['ir.model.fields'].search([('model','=ilike',record._name),('ttype','=like',ttype)]).read()
    else:
        read_fields = env['ir.model.fields'].search([('model','=ilike',record._name)]).read()
    fields_dict = {}
    for field in read_fields:
        fields_dict[field['name']] = field

    #for i in fields_dict:
    #    print(i)
    #for key,val in fields_dict:
    #    print(key,val)
    #for i in read_fields:
    #    print(i)
        
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

                if ttype == "many2many":
                    # many2many's don't use the inverse field, instead they link to other many2many's with a table, so find the other m2m field using this table
                    if fields_dict[key]['relation_table']:
                        other_table_field = env['ir.model.fields'].search([('relation_table','=ilike',fields_dict[key]['relation_table']),('name','not ilike',key)]).name
                        inverse_string = "inverse to %s" % other_table_field
                    else:
                        inverse_string = "no inverse"
                else:
                    if fields_dict[key]['relation_field']:
                        inverse_string = "inverse to %s" % fields_dict[key]['relation_field']
                    else:
                        # if this field doesn't have the inverse set, the inverse field still may have ITS inverse set as this field
                        field_result = env['ir.model.fields'].search([('relation','=ilike',record._name), ('relation_field','=ilike',key)])
                        if field_result:
                            inverse_string = "inverse to %s" % field_result.name
                        else:
                            inverse_string = "no inverse"

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
            display(env, rec, ttype=ttype, hide_empty=hide_empty, archived=archived)