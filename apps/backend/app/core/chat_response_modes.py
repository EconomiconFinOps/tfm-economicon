"""Closed, non-documentary replies alongside evidence-backed narration.

The provider selects a generic need or grounded user arithmetic. It cannot add
documentary assertions to the branch that deliberately selects no sources.
"""
import copy


REQUESTS={
    'greeting':('no_data','Hola. Puedo ayudarte con una consulta FinOps del MVP.',
        'Indica la pregunta o el escenario que quieres analizar.'),
    'authorized_cost_data':('no_data','No dispongo de datos financieros autorizados suficientes para responder esa consulta.',
        'Aporta una fuente o consulta de costes autorizada, con período, ámbito y moneda; no compartas credenciales.'),
    'ingestion_coverage':('no_data','La ausencia de registros no demuestra un coste cero.',
        'Confirma la cobertura del período y del ámbito, completa o revisa la ingesta y vuelve a consultar los datos.'),
    'comparable_baseline':('insufficient_data','No puedo interpretar la variación sin una base comparable aplicable.',
        'Aporta el período base y el observado; si el recurso es nuevo, investiga su aparición y confirma el contexto.'),
    'clarification':('insufficient_data','Necesito concretar la consulta antes de responder de forma fundada.',
        'Indica la métrica o el concepto, el ámbito y, cuando proceda, el período y los datos del escenario.'),
    'missing_documentation':('insufficient_data','No he contrastado documentalmente la regla necesaria para esta consulta.',
        'Aporta la política o documentación aplicable y aclara el criterio que necesitas contrastar.'),
    'outside_mvp':('unsupported','Esa consulta queda fuera del alcance disponible del asistente FinOps del MVP.',
        'Reformula la consulta dentro del alcance disponible o solicita una revisión humana especializada.'),
    'execution_not_enabled':('refused','No puedo ejecutar cambios sobre los recursos desde este chat.',
        'Puedo preparar un análisis o una propuesta revisable; aporta los datos y las restricciones para que una persona autorice cualquier cambio.'),
    'temporary_unavailable':('error','No puedo completar la consulta con la información o los servicios disponibles en este momento.',
        'Vuelve a intentarlo más tarde o solicita una revisión humana si el problema persiste.'),
}


def mode(value):
    if not isinstance(value,dict):return None
    if set(value)=={'scenario'}:return 'scenario'
    if set(value)=={'request'}:return 'request'
    return None


def bind_modes(schema,quantities):
    from app.core.chat_expressions import expression_definitions
    result=copy.deepcopy(schema)
    branches=result.get('anyOf',[{key:item for key,item in result.items() if key!='$defs'}])
    base=copy.deepcopy(branches[-1])
    retained=[]
    for branch in branches:
        props=branch['properties']
        if props['answer'].get('type')=='array':
            if props['evidence'].get('maxItems')==0:continue
            props['evidence']['minItems']=1
        retained.append(branch)
    defs=result.setdefault('$defs',{})
    user={key:item for key,item in (quantities or {}).items()
          if not any(origin.get('kind')=='corpus' for origin in item.get('provenance',[]))}
    if user:
        def prefix(value):
            if isinstance(value,list):return [prefix(item) for item in value]
            if isinstance(value,dict):return {key:('#/$defs/User'+item.removeprefix('#/$defs/')
                if key=='$ref' else prefix(item)) for key,item in value.items()}
            return value
        defs.update({'User'+key:prefix(value) for key,value in expression_definitions(user).items()})
        props=copy.deepcopy(base['properties'])
        props['status']={'type':'string','const':'insufficient_data'}
        calculations={'type':'array','maxItems':8,'items':{'$ref':'#/$defs/UserRenderedExpression'}}
        values={'type':'array','maxItems':8,'items':{'type':'string','enum':list(user)}}
        alternatives=[]
        for first in ('calculations','quantities'):
            fields={'calculations':copy.deepcopy(calculations),'quantities':copy.deepcopy(values)}
            fields[first]['minItems']=1
            if first=='quantities':fields['calculations']['maxItems']=0
            alternatives.append({'type':'object','properties':fields,'required':list(fields),'additionalProperties':False})
        props['answer']={'type':'object','properties':{'scenario':{'anyOf':alternatives}},
            'required':['scenario'],'additionalProperties':False}
        for field in ('metrics','recommendations','evidence','assumptions','limitations','next_actions'):
            props[field]['minItems']=0;props[field]['maxItems']=0
        retained.append({**copy.deepcopy(base),'properties':props})
    props=copy.deepcopy(base['properties'])
    props.pop('status')
    props['answer']={'type':'object','properties':{'request':{
        'type':'object','properties':{'reason':{'type':'string','enum':list(REQUESTS)}},
        'required':['reason'],'additionalProperties':False}},'required':['request'],'additionalProperties':False}
    for field in ('metrics','recommendations','evidence','assumptions','limitations','next_actions'):
        props[field]['minItems']=0;props[field]['maxItems']=0
    request={**copy.deepcopy(base),'properties':props,'required':[key for key in base['required'] if key!='status']}
    retained.append(request)
    return ({**retained[0],'$defs':defs} if len(retained)==1 else
        {'type':'object','anyOf':retained,'$defs':defs})


def render_mode(value,expressions):
    kind=mode(value)
    if kind=='request':
        request=value['request']
        if not isinstance(request,dict) or set(request)!={'reason'} or not isinstance(request['reason'],str) or request['reason'] not in REQUESTS:
            raise ValueError('Invalid neutral request.')
        return REQUESTS[request['reason']][1]
    if kind!='scenario' or expressions is None:raise ValueError('Invalid user scenario.')
    scenario=value['scenario']
    if not isinstance(scenario,dict) or set(scenario)!={'calculations','quantities'}:
        raise ValueError('Invalid user scenario.')
    calculations=scenario['calculations'];values=scenario['quantities']
    if (not isinstance(calculations,list) or not isinstance(values,list) or len(calculations)>8
            or len(values)>8 or not (calculations or values)):
        raise ValueError('Invalid user scenario.')
    parts=['Escenario hipotético aportado; no verificado financieramente.\n']
    for key in values:parts.append(expressions.render_quantity(key))
    for node in calculations:parts.append(expressions.render(node))
    if expressions.documentary_sources:raise ValueError('User scenario contains documentary operands.')
    from app.core.chat_expressions import CURRENCIES
    def leaves(node):
        if isinstance(node,dict):
            if set(node)=={'quantity'}:return [node['quantity']]
            return [key for item in node.values() for key in leaves(item)]
        return []
    used=[*values,*[key for node in calculations for key in leaves(node)]]
    currencies={expressions.catalog[key]['unit'].split('/')[0].upper() for key in used
        if expressions.catalog[key]['unit'].split('/')[0].upper() in CURRENCIES}
    if len(currencies)>1:
        parts.append('\nLos importes de divisas distintas se mantienen separados. Para agregarlos necesito la moneda de destino, el tipo y la dirección del cambio y su fecha; no hay una conversión autorizada.\n')
    answer=''.join(parts).strip()
    if len(answer)>4000:raise ValueError('Rendered text limit.')
    return answer
