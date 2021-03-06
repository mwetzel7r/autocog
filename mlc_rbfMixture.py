'''
RBF Mixture Model trained with gradient descent; except this time you update weights that determine the covarience matrix of each hidden nodes
'''
## std lib

## ext requirements
import autograd.numpy as np 
from autograd import grad

softmax = lambda x: np.exp(x) / np.sum(np.exp(x))


def forward(params, inputs = None, hps = None):

    hidden_activation = np.exp(
        -np.einsum(
            'hif,fh->ih',
            ((inputs - params['input']['hidden']['bias']) @ params['input']['cov']['weights'] ) ** 2,
            params['input']['hidden']['weights']
        )
    )

    output_activation = hps['output_activation'](
        hidden_activation @ params['hidden']['output']['weights']
    )

    return [hidden_activation, output_activation]


## negative log likelihood function
def loss(params, inputs = None, targets = None, hps = None):
    return -np.sum(
        targets * np.log(forward(params, inputs = inputs, hps = hps)[-1]),
    ) / targets.shape[0]

## optimization function
loss_grad = grad(loss)


# - - - - - - - - - - - - - - - - - -


def build_params(num_features, num_hidden_nodes, categories, weight_range = [-.1, .1]):
    '''
    num_features <-- (numeric) number of feature in the dataset
    num_hidden_nodes <-- (numeric)
    categories <-- (list) list of category labels to use as keys for decode -- output connections
    weight_range = [-.1,.1] <-- (list of numeric)
    '''

    return {
        'input': {
            'hidden': {
                'weights': np.full([num_features, num_hidden_nodes],10.0),
                'bias': np.random.normal(*weight_range, [num_hidden_nodes, 1, num_features])
            },
            'cov': {'weights': np.array([np.eye(num_features) for h in range(num_hidden_nodes)])},
        },
        'hidden': {
            'output': {
                'weights': np.random.normal(*weight_range, [num_hidden_nodes, len(categories)]),
                'bias': np.random.normal(*weight_range, [1, len(categories)]),
            },
        },
        'attn': .5,
    }


def update_params(params, gradients, lr):
    # params['input']['hidden']['weights'] -= lr * gradients['input']['hidden']['weights'] # <-- turned this off for stability reasons (maybe they can be learned too)
    params['input']['hidden']['bias'] -= lr * gradients['input']['hidden']['bias']

    params['input']['cov']['weights'] -= .05 * gradients['input']['cov']['weights']
    # for h in range(params['input']['cov']['weights'].shape[0]): np.fill_diagonal(params['input']['cov']['weights'][h], 1)

    params['hidden']['output']['weights'] -= lr * gradients['hidden']['output']['weights']

    # params['attn'] -= lr * gradients['attn']


    # for layer in params:
        # for connection in params[layer]:
            # params[layer][connection]['weights'] -= lr * gradients[layer][connection]['weights']
            # if layer == 'input': params[layer][connection]['bias'] -= lr * gradients[layer][connection]['bias']
    return params


# - - - - - - - - - - - - - - - - - -


if __name__ == '__main__':

    cmap_ = 'binary'

    hps = {
        'lr': .5,  # <-- learning rate
        'wr': [.5, .1],  # <-- weight range
        'num_hidden_nodes': 3,

        'output_activation': lambda x: softmax(x)
        # 'output_activation': lambda x: 1 / (1 + np.exp(-x)),
        # 'output_activation': lambda x: np.exp(-(x ** 2)),
    }


    cv = -.004
    inputs = np.concatenate([
        np.random.multivariate_normal(
            [.2,.4], 
            [
                [.005,cv],
                [cv,.005],
            ],
            [50]
        ),
        np.random.multivariate_normal(
            [.6,-.2], 
            [
                [.005,-cv],
                [-cv,.005],
            ],
            [50]
        ),
        np.random.multivariate_normal(
            [.8,.8], 
            [
                [.005,cv],
                [cv,.005],
            ],
            [50]
        )
    ])
    labels = [0] *100 + [1] * 50
    cm = {0:'orange',1:'blue'}


    categories = np.unique(labels)
    idx_map = {category: idx for category, idx in zip(categories, range(len(categories)))}
    
    labels_indexed = [idx_map[label] for label in labels]
    one_hot_targets = np.eye(len(categories))[labels_indexed]

    params = build_params(
        inputs.shape[1],  # <-- num features
        hps['num_hidden_nodes'],
        categories,
        weight_range = hps['wr']
    )
    # params['input']['hidden']['bias'] = np.array([
    #     [.2,.5,.8],
    #     [.2,.5,.8],
    # ])

    num_epochs = 500

    print('loss initially: ', loss(params, inputs = inputs, targets = one_hot_targets, hps = hps))

    for epoch in range(num_epochs):
        gradients = loss_grad(params, inputs = inputs, targets = one_hot_targets, hps = hps)
        params = update_params(params, gradients, hps['lr'])
    print('loss after training: ', loss(params, inputs = inputs, targets = one_hot_targets, hps = hps))
    print('model accuracy:', 
        np.mean(
            np.equal(
                np.argmax(
                    forward(params, inputs = inputs, hps = hps)[-1],
                    axis = 1,
                ),
                labels
            )
        )
    )






    import matplotlib.pyplot as plt 
    from mpl_toolkits import mplot3d
    from matplotlib.gridspec import GridSpec

    clean = lambda ax: [ax.set_yticks([]), ax.set_xticks([])]
    clean3d = lambda ax: [ax.set_yticks([]), ax.set_xticks([]), ax.set_zticks([])]


    g = 100
    m1, m2 = [-1,2]
    xx, yy = np.meshgrid(np.linspace(m1,m2,g), np.linspace(m1,m2,g))
    mesh = np.array([xx,yy]).reshape(2, g*g).T
    
    fig = plt.figure(
        figsize = [8,4]
    )
    gs = GridSpec(1,2)

    hidden_activation, output_activation = forward(params, inputs = mesh, hps = hps)


    ##__Surface Plot
    surface_ax = plt.subplot(gs[:,0], projection = '3d')
    surface_ax.plot_surface(
        xx, 
        yy,
        np.flip(hidden_activation.sum(axis = 1).reshape(g,g), axis = 0),
        alpha = .5, cmap = 'viridis',
    )
    clean3d(surface_ax)
    surface_ax.set_title('Surface')



    ##__Flat Plot
    flat_ax = plt.subplot(gs[:,1])
    flat_ax.imshow(
        np.flip(hidden_activation.sum(axis = 1).reshape(g,g), axis = 0),
        cmap = 'viridis', extent = [m1,m2,m1,m2],
    )
    flat_ax.scatter(
        *inputs.T,
        c = ['purple' if l == 0 else 'orange' for l in labels]
    )
    clean(flat_ax)
    flat_ax.set_title('Imshow')


    # plt.show()
    plt.savefig('test.png')

