"""
Main module
"""

from clize import run, parameters
import data
import settings

logger = settings.logger.getChild('main')

def test_iterators():
    logger.info('Starting...')

    loader = data.Loader()
    train_data = loader.load_crop_images(data_type = 'region_crops')
    #train_data = loader.load_original_images()
    train_val_split = loader.train_val_split(train_data)

    #transform = data.LoadTransformer(data.AugmentationTransformer(next = data.ResizeTransformer(settings.TRANSFORMATION_RESIZE_TO)))
    transform = data.LoadTransformer(data.AugmentationTransformer(next = data.ResizeTransformer((224,224,3))))
    #transform = data.AugmentationTransformer(next = data.ResizeTransformer((224,224,3)))
    iterator = data.DataIterator(train_val_split['train'], transform, batch_size = 16, shuffle = True, seed = 42)
    
    for i in range(10):
        batch = next(iterator)
        print('First in batch: {0}'.format(batch[0].shape))
        print('Batch size: {0}'.format(len(batch)))

def test_density_map_feature_loading():
    import utils
    import matplotlib.pyplot as plt

    logger.info('Starting...')

    loader = data.Loader()
    density_data = loader.load_density_map_feature_crops()
    
    for img in density_data:
        logger.info('Image %s: %s feature(s)' % (img['meta']['image_name'], len(img['features'])))
        coords = img['meta']['coordinates']

        map = utils.sea_lion_density_map(img['meta']['patch']['width'] / 2, img['meta']['patch']['height'] / 2, coords, sigma = 35, scale = 0.5)
        logger.info("sum of density map: %s" % sum(sum(map)))

        blurred = img['features']['gs']['3.5']()

        plt.subplot(1,3,1)
        plt.imshow(blurred.astype("uint8"))
        plt.axis('off')
        plt.subplot(1,3,2)
        plt.imshow(map, interpolation='nearest', cmap='viridis')
        plt.axis('off')
        plt.subplot(1,3,3)
        plt.imshow(blurred.astype("uint8"))
        plt.imshow(map, interpolation='nearest', cmap='viridis', alpha=0.5)
        plt.axis('off')
        plt.show()

def test_full_feature_map_loading():
    import matplotlib.pyplot as plt

    loader = data.Loader()
    
    features = loader.load_full_size_feature_images('test_st1')

    for img in features:
        logger.info('Image %s: %s feature(s)' % (img['meta']['image_name'], len(img['features'])))
        #coords = img['meta']['coordinates']

        blurred = img['features']['gs']['3.5']()
        #shape = blurred.shape

        #map = utils.sea_lion_density_map(shape[1], shape[0], coords, sigma = 35)

        plt.imshow(blurred.astype("uint8"))
        plt.show()

        #plt.subplot(1,3,1)
        #plt.imshow(blurred.astype("uint8"))
        #plt.axis('off')
        #plt.subplot(1,3,2)
        #plt.imshow(map, interpolation='nearest', cmap='viridis')
        #plt.axis('off')
        #plt.subplot(1,3,3)
        #plt.imshow(blurred.astype("uint8"))
        #plt.imshow(map, interpolation='nearest', cmap='viridis', alpha=0.5)
        #plt.axis('off')
        #plt.show()
        pass

def test_pdf():
    import utils
    import matplotlib.pyplot as plt
    import functools

    dx = [0.01, 0.01]
    pdf = utils.get_multivariate_normal_pdf(x = [[-10, 10], [-10, 10]], dx = dx, mean = [-3, -4], cov = [[2.5, 0], [-0.9, 5.0]])
    logger.info("The density sums to %s." % (sum(sum(pdf)) * functools.reduce(lambda x, y: x * y, dx, 1.0)))

    plt.imshow(pdf)
    plt.show()
    pass

def test_density_map():
    import utils
    import matplotlib.pyplot as plt

    loader = data.Loader()
    coords = loader.get_train_original_coordinates()

    for img_coords in coords.values():
        map = utils.sea_lion_density_map(1000, 700, img_coords, sigma = 35, scale = 0.25)

        logger.info("sum of density map: %s" % sum(sum(map)))

        plt.imshow(map, interpolation='nearest', cmap='viridis')
        plt.show()

def generate_test_set_counts_from_coordinates():
    import estimate_count
    estimate_count.from_coordinates()
        
def generate_heatmap_crops(max_overlap_perc:float):
    crop_size = 400
    attention = False
    output_size = 224

    import cropping
    crp = cropping.RegionCropper(crop_size = crop_size,
                                 attention = attention,
                                 output_size = output_size)
    crp.find_all_crops(max_overlap_perc = max_overlap_perc)
   
def generate_region_crops(min_sealions_pos:int, blackout:bool):
    #python3 main.py generate-region-crops 5 True
    import cropping
    
    output_size = 224
    crop_size = 400
    diameter = 100
    cropper = cropping.RegionCropper(crop_size = crop_size, attention = blackout, diameter = diameter, output_size = output_size)

    sliding_perc = 0.1
    max_overlap_perc = 0.5
    plot = False
    cropper.find_pos_crops_dataset(min_sealions_pos, max_overlap_perc, plot, sliding_perc)

    wanted_crops = 70000
    max_sealions_neg = 0
    cropper.find_neg_crops_dataset(wanted_crops, max_sealions_neg)

def generate_individual_crops(num_negative_crops:int, *, sea_lion_size=100, ignore_pups=False, blackout=False, blackout_diameter=100):
    #python3 main.py generate-individual-crops 20000
    """
    Create positive and negative crops of sea lions from the original training data.
    
    num_negative_crops: the total number of negative crops generated over the whole data set
    
    sea_lion_size: the width and height of a sea lion crop in the image (always square)
    
    ignore_pups: if true, no pups are included in the data set (neither in positive nor negative samples)
    
    blackout: if true, the crops' corners will be made black and only a circle will remain

    blackout_diameter: the diameter of the blackout mask (only used if blackout = True)
    """
    import cropping
    cropping.generate_individual_crops(sea_lion_size, num_negative_crops, ignore_pups, blackout, blackout_diameter)

def generate_overlap_masks():
    #python3 main.py generate-overlap-masks
    """
    Generate boolean masks for the training set's black regions,
    in which False indicates that a pixel is black (overlaps with another image).
    Do this before generating crops.
    """
    
    import cropping
    cropping.generate_overlap_masks()

def generate_heatmaps(dataset:parameters.one_of('train', 'test_st1'), network_type:parameters.one_of('region', 'individual')):
    """
    Generate fully convolutional heatmaps 
    
    dataset: the data set to apply it to ('train' or 'test_st1')
    
    network_type: type of network to apply it to ('region' or 'individual')
    """
    import heatmap
    heatmap.generate_heatmaps(dataset, network_type)

def generate_features(dataset:parameters.one_of('train', 'test_st1'), *, start=0, end=-1, patches=False, ignore_pups=False):
    """
    Generate features for the given part of the data set 
    
    dataset: the data set to apply it to ('train' or 'test_st1')
    
    start: the first image ID to generate features of
    
    end: the last image ID to generate features of, *exclusive* (e.g., 0-1000 generates features for 0,1,...,999). -1 indicates the end of the data set
    
    patches: if set to true, only random patches of each image are converted to features. Can only be combined with 'train'
    
    ignore_pups: if set to true, pups are not counted in positive crops
    """
    if patches and dataset != 'train':
        raise Exception('patches can only be used with the training set')
    
    import feature
    feature.run_feature_generation(dataset, start, end, patches, ignore_pups)


# "network": (# layers frozen in finetuning, network file to continue with)
# numbers taken from previous project, might need to be changed
NETWORKS = {
    'vgg16':     (0,   'vgg16-lay2-ep018-tloss0.5491-vloss0.5485.hdf5'),
    'vgg19':     (17,  'insert-vgg19-network-weights-file-here.hdf5'),
    'inception': (125, 'insert-inception-network-weights-file-here.hdf5'), # no numbers for this one
    'xception':  (125, 'xception-lay53-heatmap_crops-ep030-tloss647.2298-vloss636.6220.hdf5'),
    'resnet':    (75,  'resnet-lay2-ep016-tloss0.0832-vloss0.0521.hdf5')
}

def train_top_network(task:parameters.one_of('binary', 'type','odm'), network:parameters.one_of(*sorted(NETWORKS.keys())), data_type:parameters.one_of('original', 'sea_lion_crops', 'region_crops','heatmap_crops')):
    #nice -19 python3 main.py train-top-network binary vgg16 region_crops
    """
    Train the top dense layer of an extended network.
    
    task: the task to train for ("binary" for sea lion or not, "type" for sea lion type)
    
    network: the network architecture to train (VGG16, VGG19, Inception, XCeption, ResNet)
    
    data_type: which data to use as training/validation set ("original", "sealion_crops", "region_crops")
    """

    from network import TransferLearning, TransferLearningSeaLionOrNoSeaLion, TransferLearningSeaLionHeatmap
    
    if data_type == 'original':
        input_shape = settings.TRANSFORMATION_RESIZE_TO
    elif data_type == 'sea_lion_crops':
        input_shape = (197,197,3)
    elif data_type == 'region_crops':
        input_shape = (224,224,3)
    elif data_type == 'heatmap_crops':
        input_shape = (224,224,3)

    if task == 'type':
        tl = TransferLearning(data_type = data_type, input_shape = input_shape, prediction_class_type = "multi", mini_batch_size=16)
    elif task == 'binary':
        tl = TransferLearningSeaLionOrNoSeaLion(data_type = data_type, input_shape = input_shape, prediction_class_type = "single", mini_batch_size=64, tensor_board = True)
    elif task == 'odm':
        tl = TransferLearningSeaLionHeatmap(data_type = data_type, input_shape = input_shape, prediction_class_type = task, mini_batch_size=64, tensor_board = True, class_balancing = False)
    tl.build(network.lower(), input_shape = input_shape)
    tl.train_top(epochs = 400)

def fine_tune_network(task:parameters.one_of('binary', 'type','odm'), network:parameters.one_of(*sorted(NETWORKS.keys())), data_type:parameters.one_of('original', 'sea_lion_crops', 'region_crops')):
    """
    Fine-tune a trained extended network. To do this, first the top
    of the extended network must have been trained.
    
    task: the task to train for ("binary" for sea lion or not, "type" for sea lion type)
    
    network: the network architecture to train (VGG16, VGG19, Inception, XCeption, ResNet)
    
    data_type: which data to use as training/validation set ("original", "sealion_crops", "region_crops")
    """

    from network import TransferLearning, TransferLearningSeaLionOrNoSeaLion, TransferLearningSeaLionHeatmap

    if data_type == 'original':
        input_shape = settings.TRANSFORMATION_RESIZE_TO
    elif data_type == 'sea_lion_crops':
        input_shape = (197,197,3)
    elif data_type == 'region_crops':
        input_shape = (224,224,3)
    
    if task == 'type':
        tl = TransferLearning(data_type = data_type, input_shape = input_shape, prediction_class_type = "multi", mini_batch_size=16)
    elif task == 'binary':
        tl = TransferLearningSeaLionOrNoSeaLion(data_type = data_type, input_shape = input_shape, prediction_class_type = "single", mini_batch_size=64)
    elif task == 'odm':
        tl = TransferLearningSeaLionHeatmap(data_type = data_type, input_shape = input_shape, prediction_class_type = task, mini_batch_size=64, tensor_board = True, class_balancing = False)

    tl.build(network.lower(), input_shape = input_shape)

    tl.fine_tune_extended(
        epochs = 200,
        input_weights_name = None,#NETWORKS[network.lower()][1],
        n_layers = NETWORKS[network.lower()][0])

def fine_tune_network_perc(task:parameters.one_of('binary', 'type','odm'), network:parameters.one_of(*sorted(NETWORKS.keys())), perc:float, data_type:parameters.one_of('original', 'sealion_crops', 'region_crops','heatmap_crops')):
    #python3 main.py fine-tune-network-perc odm xception 0.35 heatmap_crops
    """
    Fine-tune a trained extended network. To do this, first the top
    of the extended network must have been trained.
    
    task: the task to train for ("binary" for sea lion or not, "type" for sea lion type)
    
    network: the network architecture to train (VGG16, VGG19, Inception, XCeption, ResNet)
    
    data_type: which data to use as training/validation set ("original", "sealion_crops", "region_crops")
    """

    from network import TransferLearning, TransferLearningSeaLionOrNoSeaLion, TransferLearningSeaLionHeatmap

    if data_type == 'original':
        input_shape = settings.TRANSFORMATION_RESIZE_TO
    elif data_type == 'sea_lion_crops':
        input_shape = (197,197,3)
    elif data_type == 'region_crops':
        input_shape = (224,224,3)
    elif data_type == 'heatmap_crops':
        input_shape = (224, 224, 3)
    
    if task == 'type':
        tl = TransferLearning(data_type = data_type, input_shape = input_shape, prediction_class_type = "multi", mini_batch_size=16)
    elif task == 'binary':
        tl = TransferLearningSeaLionOrNoSeaLion(data_type = data_type, input_shape = input_shape, prediction_class_type = "single", mini_batch_size=64)
    elif task == 'odm':
        tl = TransferLearningSeaLionHeatmap(data_type = data_type, input_shape = input_shape, prediction_class_type = task, mini_batch_size=64, tensor_board = True, class_balancing = False)

    tl.build(network.lower(), input_shape = input_shape)

    tl.fine_tune_extended(
        epochs = 200,
        input_weights_name = NETWORKS[network.lower()][1],
        perc = perc)

def train_density_network():
    from network import DensityLearning
    network = DensityLearning(data_type = "density_map_feature_crops", class_balancing = False, mini_batch_size=16)
    network.build()
    network.train(epochs = 100)

def predict_density_network(*, plot = True, save = False, start = 0, end = -1):
    import numpy as np
    import scipy
    import keras.models
    import data
    import metrics
    import layers

    if plot:
        import matplotlib.pyplot as plt

    if save:
        import os, gzip, pickle
        if not os.path.exists(settings.PREDICTED_DENSITY_MAPS_DIR):
            os.makedirs(settings.PREDICTED_DENSITY_MAPS_DIR)

    network = keras.models.load_model(settings.DENSITY_NETWORK_WEIGHTS, custom_objects = {
        'mae2d': metrics.mae2d,
        "per_pixel_squared_error": metrics.per_pixel_squared_error,
        'positive_mae': metrics.positive_mae,
        'mae_per_class': metrics.mae_per_class,
        'count_diff': metrics.count_diff,
        'DensityCount': layers.DensityCount})
    loader = data.Loader()
    feature_transformer = data.LoadDensityFeatureTransformer()

    imgs = loader.load_full_size_feature_images('test_st1')

    if end == -1:
        end = len(imgs) - 1

    for idx in range(start, end+1):
        img = imgs[idx]

        d = feature_transformer.apply(img)
        y = network.predict(np.expand_dims(d['x'], axis=0))
        y_img = y[0]
        y_img = y_img[0,:,:,0]
        y_count = y[1]

        logger.info('Sum of density, calculated: %s from network: %s' % (sum(sum(y_img)), y_count))


        if save:
            fp = gzip.open(os.path.join(settings.PREDICTED_DENSITY_MAPS_DIR, "%s.data" % img['meta']['image_name']), 'wb')
            pickle.dump(y, fp)
            fp.close()

        if plot:
            gs = img['features']['gs']['0.7']()
            plt.subplot(1,3,1)
            plt.imshow(gs.astype('uint8'))
            plt.axis('off')
            plt.subplot(1,3,2)
            plt.imshow(y_img, interpolation='nearest', cmap='viridis')
            plt.subplot(1,3,3)
            plt.imshow(gs.astype('uint8'))
            y_resized = scipy.misc.imresize(y_img, gs.shape)
            plt.imshow(y_resized, interpolation='nearest', cmap="viridis", alpha=0.5)
            plt.show()


if __name__ == '__main__':
    run(test_iterators,
        test_density_map_feature_loading,
        test_pdf,
        test_density_map,
        test_full_feature_map_loading,
        generate_test_set_counts_from_coordinates,
        generate_region_crops,
        generate_individual_crops,
        generate_heatmap_crops,
        generate_overlap_masks,
        generate_heatmaps,
        generate_features,
        train_top_network,
        fine_tune_network,
        fine_tune_network_perc,
        train_density_network,
        predict_density_network)
