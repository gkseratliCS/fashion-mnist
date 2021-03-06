import numpy as np
import tensorflow as tf
from sklearn.utils import shuffle
from selu import *

tf.logging.set_verbosity(tf.logging.INFO)

from tensorflow.examples.tutorials.mnist import input_data

DATA_DIR = './data/fashion'

def cnn_model_fn(features, labels, mode):
    """Model function for CNN."""
    input_layer = tf.reshape(features["x"], [-1, 28, 28, 1])
    conv1 = tf.layers.conv2d(
        inputs=input_layer, filters=64, kernel_size=[5, 5],
        padding="same", activation=tf.nn.relu)
    conv2 = tf.layers.conv2d(
        inputs=conv1, filters=64, kernel_size=[5, 5],
        padding="same", activation=tf.nn.relu)
    pool1 = tf.layers.max_pooling2d(
        inputs=conv2, pool_size=[2, 2], strides=2)
    conv3 = tf.layers.conv2d(
        inputs=pool1, filters=64, kernel_size=[5, 5],
        padding="same", activation=tf.nn.relu)
    conv4 = tf.layers.conv2d(
        inputs=conv3, filters=64, kernel_size=[5, 5],
        padding="same", activation=tf.nn.relu)
    pool2 = tf.layers.max_pooling2d(
        inputs=conv4, pool_size=[2, 2], strides=2)
    pool2_flat = tf.reshape(pool2, [-1, 7 * 7 * 64])
    dense1 = tf.layers.dense(inputs=pool2_flat, units=128, activation=tf.nn.relu)
    dropout1 = tf.layers.dropout(
        inputs=dense1, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)
    dense2 = tf.layers.dense(inputs=dropout1, units=128, activation=tf.nn.relu)
    dropout2 = tf.layers.dropout(
        inputs=dense2, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)
    logits = tf.layers.dense(inputs=dropout2, units=10)

    predictions = {
        "classes": tf.argmax(input=logits, axis=1),
        "probabilities": tf.nn.softmax(logits, name="softmax_tensor")
    }
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)

    # Calculate Loss (for both TRAIN and EVAL modes)
    onehot_labels = tf.one_hot(indices=tf.cast(labels, tf.int32), depth=10)
    loss = tf.losses.softmax_cross_entropy(
        onehot_labels=onehot_labels, logits=logits)

    # Configure the Training Op (for TRAIN mode)
    if mode == tf.estimator.ModeKeys.TRAIN:
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01)
        train_op = optimizer.minimize(
            loss=loss,
            global_step=tf.train.get_global_step())
        tf.summary.scalar('loss', loss)
        accuracy = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(logits, 1), tf.argmax(onehot_labels, 1)), tf.float32))
        tf.summary.scalar('accuracy', accuracy)
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)

    # Add evaluation metrics (for EVAL mode)
    eval_metric_ops = {
        "accuracy": tf.metrics.accuracy(
            labels=labels, predictions=predictions["classes"])}
    return tf.estimator.EstimatorSpec(
        mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)


def main(unused_argv):
    # Load training and eval data
    mnist = input_data.read_data_sets(DATA_DIR, one_hot=False, validation_size=0)
    train_data = mnist.train.images  # Returns np.array
    train_labels = np.asarray(mnist.train.labels, dtype=np.int32)
    train_data, train_labels = shuffle(train_data, train_labels)
    eval_data = mnist.test.images  # Returns np.array
    eval_labels = np.asarray(mnist.test.labels, dtype=np.int32)
    eval_data, eval_labels = shuffle(eval_data, eval_labels)

    # Create the Estimator
    mnist_classifier = tf.estimator.Estimator(
        model_fn=cnn_model_fn, model_dir="model/fashion_selu_large_lr001")

    # Train the model
    train_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": train_data},
        y=train_labels,
        batch_size=500,
        num_epochs=None,
        shuffle=True)

    # Evaluate the model and print results
    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": eval_data},
        y=eval_labels,
        num_epochs=1,
        shuffle=False)

    predict_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": eval_data},
        y=eval_labels,
        num_epochs=1,
        shuffle=False)

    for j in range(100):
        mnist_classifier.train(
            input_fn=train_input_fn,
            steps=100)
        eval_results = mnist_classifier.evaluate(input_fn=eval_input_fn)
        print(eval_results)
        '''
        predictions = list(mnist_classifier.predict(input_fn=eval_input_fn))
        print("Num of Samples :", len(predictions))
        '''
if __name__ == "__main__":
    tf.app.run()
