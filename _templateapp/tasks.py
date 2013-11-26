from celery.task import task

# With this decorator you can define any function as a Celery task
# The parameter 'name' is not required (it would take the function's name
# if not defined), but is a good practice to add a namespace.
@task(name='_templateapp.add')
def simple_task(n):
    '''
    Example of a really simple Celery task.
    Call it like this:
    simple_task.delay(2)
    '''
    return n+1