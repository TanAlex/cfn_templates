exports.start = (event, context, callback) => {
    console.log('start event', event);
    console.log('start context', context);
    callback(undefined, { function: 'start' });
};
exports.wait3000 = (event, context, callback) => {
    console.log('wait3000 event', event);
    console.log('wait3000 context', context);
    setTimeout(() => {
        callback(undefined, { function: 'wait3000' });
    }, 3000);
};
exports.wait500 = (event, context, callback) => {
    console.log('wait500 event', event);
    console.log('wait500 context', context);
    setTimeout(() => {
        callback(undefined, { function: 'wait500' });
    }, 500);
};
exports.end = (event, context, callback) => {
    console.log('end event', event);
    console.log('end context', context);
    callback(undefined, { function: 'end' });
};