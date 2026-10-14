"""Private response basis; public response strings and financial authority stay unchanged."""
import copy

BASIS_STATUSES={
    'user_scenario':('insufficient_data',),
    'missing_data':('no_data','insufficient_data','error'),
    'clarification':('insufficient_data',),
    'refusal':('unsupported','refused'),
    'greeting':('no_data',),
}
DOCUMENTARY_BASES=('missing_data','clarification','refusal')
BASIS_DESCRIPTIONS={
    'user_scenario':'Explain the supplied hypothetical data, labels, scope and calculations; no documentary policies or verified financial claims.',
    'missing_data':'Explain the answerable part and the specific unavailable data; request a useful next step, without claiming documents do not exist. Select pertinent authorized documentary citations when used.',
    'clarification':'Explain the ambiguity and ask a precise useful clarification, citing authorized documentary support when used.',
    'refusal':'Explain unavailable execution or an unrelated domain, and offer a useful reviewable next step; select pertinent authorized documentary citations when used.',
    'greeting':'Respond to a greeting without financial or documentary claims.',
}
USER_PREFIX='Escenario hipotético aportado; no verificado financieramente.\n'


def response_prefix(basis):
    if basis is not None and basis not in (*BASIS_STATUSES,'authorized_evidence'):
        raise ValueError('Invalid response basis.')
    return USER_PREFIX if basis=='user_scenario' else ''


def bind_modes(schema,quantities):
    from app.core.chat_expressions import expression_definitions
    result=copy.deepcopy(schema)
    branches=result.get('anyOf',[{key:item for key,item in result.items() if key!='$defs'}])
    base=next(copy.deepcopy(branch) for branch in branches if branch['properties']['answer'].get('type')=='array')
    retained=[]
    for branch in branches:
        props=branch['properties']
        if props['answer'].get('type')=='array':
            if props['evidence'].get('maxItems')==0:continue
            props['evidence']['minItems']=1
            props['basis']={'type':'string','const':'authorized_evidence',
                'description':'Claims backed by the selected authorized sources, including financial sources only when server-authorized.'}
            branch['properties']={'basis':props.pop('basis'),**props}
            branch['required']=[*branch['required'],'basis']
        retained.append(branch)
    defs=result.setdefault('$defs',{})
    user={key:item for key,item in (quantities or {}).items()
          if not any(origin.get('kind')=='corpus' for origin in item.get('provenance',[]))}
    choices=[{'type':'object','properties':{'inference':{'type':'string','maxLength':3982}},'required':['inference'],'additionalProperties':False}]
    if user:
        def prefix(value):
            if isinstance(value,list):return [prefix(item) for item in value]
            if isinstance(value,dict):return {key:('#/$defs/User'+item.removeprefix('#/$defs/') if key=='$ref' else prefix(item)) for key,item in value.items()}
            return value
        defs.update({'User'+key:prefix(value) for key,value in expression_definitions(user).items()})
        choices.extend([
            {'type':'object','properties':{'quantity':{'type':'string','enum':list(user)}},'required':['quantity'],'additionalProperties':False},
            {'type':'object','properties':{'expression':{'$ref':'#/$defs/UserRenderedExpression'}},'required':['expression'],'additionalProperties':False}])
    for basis,statuses in BASIS_STATUSES.items():
        props=copy.deepcopy(base['properties'])
        props['basis']={'type':'string','const':basis,'description':BASIS_DESCRIPTIONS[basis]}
        props['status']={'type':'string','enum':list(statuses)}
        options=copy.deepcopy(choices)
        if basis in DOCUMENTARY_BASES:
            from app.core.chat_claims import documentary_schema
            documentary=documentary_schema(getattr(quantities,'authorized_sources',getattr(quantities,'rule_sources',())))
            if documentary:options.append(documentary)
        if basis=='greeting':options=[{'type':'object','properties':{'text':{'type':'string','maxLength':4000}},'required':['text'],'additionalProperties':False}]
        props['answer']={'type':'array','minItems':1,'maxItems':128,'items':options[0] if len(options)==1 else {'anyOf':options}}
        for field in ('metrics','recommendations'):
            props[field]['minItems']=0;props[field]['maxItems']=0
        props['evidence']['minItems']=0
        if basis not in DOCUMENTARY_BASES:props['evidence']['maxItems']=0
        if basis in ('user_scenario','greeting'):
            # These modes cannot consume documentary authority in *any* field.
            # Inheriting the general auxiliary schema advertised excerpts that
            # render_response necessarily rejects after generation.
            for field in ('assumptions','limitations','next_actions'):
                props[field]['items']={'type':'array','minItems':1,'maxItems':1,
                    'items':{'type':'object','properties':{
                        'inference':{'type':'string','maxLength':482}},
                        'required':['inference'],'additionalProperties':False}}
        if basis in ('missing_data','clarification','refusal'):props['next_actions']['minItems']=1
        retained.append({**copy.deepcopy(base),'properties':{'basis':props.pop('basis'),**props},'required':[*base['required'],'basis']})
    return {'type':'object','anyOf':retained,'$defs':defs}
