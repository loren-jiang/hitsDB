from . import factories as logFactories

def make_users_and_groups(n=5, k=5):
    """
    Make a set of users and groups and returns them
    """
    groups = []
    users = []
    num_groups = n
    num_users_per_iteration = k
    groups.extend(logFactories.GroupFactory.create_batch(num_groups))
    for i in range(num_groups):
        sliced_groups = groups[i:num_groups]
        for k in range(num_users_per_iteration):
            users.append(logFactories.UserFactory(groups=sliced_groups))
    return {
        'groups':groups, 
        'users':users
    }
