/**
 * TheVirtualBrain-Framework Package. This package holds all Data Management, and 
 * Web-UI helpful to run brain-simulations. To use it, you also need do download
 * TheVirtualBrain-Scientific Package (for simulators). See content of the
 * documentation-folder for more details. See also http://www.thevirtualbrain.org
 *
 * (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
 *
 * This program is free software; you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation. This program is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for more details. You should have received a copy of the GNU General 
 * Public License along with this program; if not, you can download it here
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0
 *
 **/

// //it contains all the points that have to be/have been displayed (it contains all the points from the read file);
// //it is an array of arrays (each array contains the points for a certain line chart)
var AG_allPoints = [];
// it supplies the labels for x axis (time in milliseconds)
var AG_time = [];
//it is used for clearing timing events (the event that calls the drawGraph method after a specified time-interval)
var t = null;
//how many elements will be visible on the screen
//computed on the server
var AG_numberOfVisiblePoints = 0;
//all the points that are visible on the screen at a certain moment; the points are read from the <code>AG_allPoints</code> array
//and are translated with a value equal to [AG_translationStep * (AG_noOfLines - the index of the current line)]
//THE FORM of this matrix is: [ [[t1, a1], [t2, a2], ...], [[t1, b1], [t2, b2], ...], ..., [[t1, n1], [t2, n2], ...]]
// t1, t2, ... - represents time that is visible on the screen at a certain moment;
// a1, a2,... - represents the translated values
var AG_displayedPoints = [];
//All the times values that are displayed at a certain moment. To be used by the vertical time line.
var AG_displayedTimes = [];
//the last element that was displayed on the screen is located at this index; the index refers to <code>AG_allPoints</code> array
var AG_currentIndex = 0;
//this var should be set to the length of the <code>AG_allPoints</code> array
var AG_noOfLines = 0;
// the step used for translating the drawn line charts; we translate the drawn line charts because we don't want them to overlap
// the lines will be translated with <code>AG_translationStep * AG_computedStep</code>
var AG_translationStep = 1;
// this var is computed on the server. It is used for line translation (<code>AG_translationStep * AG_computedStep</code>).
var AG_computedStep = 50;
//The normalization steps for each of the channels, in order to bring them centered near the channel bar
var AG_normalizationSteps = [];
//If the animation is paused using pause/start button
var AG_isStopped = false;
//If animation speed is set at a 0 value
var AG_isSpeedZero = false;
//the number of points that are shifted/unshift at a moment
var noOfShiftedPoints = 1;
// List of channels that will be submited on a change of the displayed channels
var AG_submitableSelectedChannels = [];
// contains the indexes of the channels that are displayed
var displayedChannels = [];
// a list of urls pointing to the files from where we should read the time
var timeSetUrls = [];
//a list containing the number of channel in each file specified in 'dataSetUrls' fields
var noOfChannelsPerSet = [];
// the number of points from the longest channel
var maxChannelLength = 0;
// the maximum number of data files from all the submited datatypes
var maxDataFileIndex = 0;
// represents the file index from the dataset that is displayed in the chart
var currentDataFileIndex = 0;
// contains the parsed data for the next file from the dataset
var nextData = [];
// contains the time for the next file from the dataset
var nextTimeData = [];
// <code>true</code> only if the next file from dataset was loaded into memory
var isNextDataLoaded = false;
// <code>true</code> only if the next time data was loaded into memory
var isNextTimeDataLoaded = false;
// <code>true</code> only if the the process of loading a file is started
var AG_isLoadStarted = false;
// this is the number of steps left before updating the next file
var threshold = 10;
// the amount of data that has passed
var totalPassedData = 0;
// the number of channels
var totalNumberOfChannels = 0;
// <code>true</code> only if any of the displayed channels contains NaN values
var nanValueFound = false;
//Channel prefix for each array of data
var channelPrefix = "Channel: ";
//
var totalTimeLength = 0;
//Default values for the x and y axis of the plot
//NOTE: do not remove from the axis AG_options 'labelWidth' and 'labelHeight' because
//this will slow down the animation
var lbl_x_width = 100;
var lbl_x_height = 30;
var zoom_range = [0.1, 20];

var AG_defaultXaxis = { zoomRange: zoom_range, labelWidth: lbl_x_width, labelHeight: lbl_x_height };
var AG_defaultYaxis = { show: false,
    		 		 zoomRange: zoom_range, labelWidth: 200, labelHeight: 30};

// the index of the cached file (the file that was loaded asynchronous)
var cachedFileIndex = 0;
var labelX = "";
var chartTitle = "";
//The displayed labels for the graph
var chanDisplayLabels = [];
// setup plot
var AG_options = {
    series: {
        shadowSize: 0,
        color: 'blue'
    }, // drawing is faster without shadows
    lines: {
        lineWidth: 1,
        show:true
    },
    yaxis: AG_defaultYaxis,
    xaxis: AG_defaultXaxis,
    grid : {
        backgroundColor: 'white',
        hoverable: true,
        clickable: true
    },
    points: {
        show: false,
        radius: 0.001
    },
    zoom: {
        interactive: false
    },
    selection: {
        mode: "xy"
    },
    legend: {
        show: false
    },
    hooks: {
        processRawData  : [processRawDataHook]
    }
};

var DEFAULT_MAX_CHANNELS = 10;
var plot = null;

var followingLine = [];
//The required position from which the following vertical time line will start moving with the array
//Expressed as a number from [0, 1], 0 - start from begining, 1 start only at end
var procentualLinePosition = 0.5;
//The actual position in the graph of the following vertical line. Start from -speed to account for the initial translation.
var currentLinePosition = 0;
//The number of points used to display the vertical line.
var numberOfPointsForVerticalLine = 1000;
var isDoubleView = false;

var AG_homeViewYValues = [];
var AG_homeViewXValues = { zoomRange: zoom_range, labelWidth: lbl_x_width, labelHeight: lbl_x_height };
//This will be set to true in the launch_viewer method called by burst small previews
var isSmallPreview = false;

var targetVerticalLinePosition;

// The base url for calling any methods on a given datatype
var baseDataURLS = [];
var nrOfPagesSet = [];
var dataPageSize = [];
var tsModes = [0, 0, 0];
var tsStates = [0, 0, 0];
var longestChannelIndex = 0;

// region selection component
var AG_regionSelector = null;

window.onresize = function() {
    var canvas = $('#EEGcanvasDiv');
    if (!isDoubleView  && !isSmallPreview ) {
		// Just use parent section width and height. For width remove some space for the labels to avoid scrolls
		// For height we have the toolbar there. Using 100% does not seem to work properly with FLOT. 				    	
    	canvas.width(canvas.parent().width() - 40);
    	canvas.height(canvas.parent().height() - 100);
    } else if (isSmallPreview) {
        canvas.width(canvas.parent().width());
        canvas.height(canvas.parent().height());
    }
    redrawPlot(plot.getData());
};

/**
 * Animated graph entry point
 */
function AG_startAnimatedChart(channelsPerSet, baseURLS, pageSize, nrOfPages,
						   timeSetPaths, step, normalizations, number_of_visible_points, nan_value_found, 
						   noOfChannels, totalLength, doubleView, channelLabels, filterGids) {

    isSmallPreview = false;
    _AG_initGlobals(channelsPerSet, baseURLS, pageSize, nrOfPages,
                    timeSetPaths, step, normalizations, nan_value_found,
                           noOfChannels, totalLength, doubleView, channelLabels);
    _AG_initPaginationState(number_of_visible_points);
    _AG_preStart();
    drawSliderForScale();
    drawSliderForAnimationSpeed();
    _AG_init_selection($.parseJSON(filterGids));
}

function AG_startAnimatedChartPreview(channelsPerSet, baseURLS, pageSize, nrOfPages,
						   timeSetPaths, step, normalizations, number_of_visible_points, nan_value_found,
						   noOfChannels, totalLength, doubleView, channelLabels) {

    isSmallPreview = true;
    AG_isStopped = true;
    _AG_initGlobals(channelsPerSet, baseURLS, pageSize, nrOfPages,
                    timeSetPaths, step, normalizations, nan_value_found,
                       noOfChannels, totalLength, doubleView, channelLabels);
    _AG_initPaginationState(number_of_visible_points);
    _AG_preStart();
    refreshChannels();
}

function AG_rePaginate(number_of_visible_points) {
    _AG_initPaginationState(number_of_visible_points);
    $('#display-page-size').html('' + number_of_visible_points);
    refreshChannels();
    if (isDoubleView){
        initActivityData();
    }
}

/**
 * Initialize global state. Part of the AG startup.
 * @private
 */
function _AG_initGlobals(channelsPerSet, baseURLS, pageSize, nrOfPages,
                           timeSetPaths, step, normalizations, nan_value_found,
                           noOfChannels, totalLength, doubleView, channelLabels){
    isDoubleView = doubleView;
    // dataSetUrls = $.parseJSON(dataSetPaths);
    baseDataURLS = $.parseJSON(baseURLS);
    nrOfPagesSet = $.parseJSON(nrOfPages);
    dataPageSize = pageSize;
    chanDisplayLabels = $.parseJSON(channelLabels);
    noOfChannelsPerSet = $.parseJSON(channelsPerSet);
    timeSetUrls = $.parseJSON(timeSetPaths);
    maxChannelLength = parseInt(pageSize);
    AG_normalizationSteps = $.parseJSON(normalizations);
    setMaxDataFileIndex(nrOfPagesSet);
    totalNumberOfChannels = noOfChannels;
    totalTimeLength = totalLength;
    if (nan_value_found == "True") {
        nanValueFound = true;
    }
    AG_computedStep = step;
}

/**
 * Initialize pagination. Part of AG startup.
 * @private
 */
function _AG_initPaginationState(number_of_visible_points){
    AG_numberOfVisiblePoints = parseInt(number_of_visible_points);
    if (AG_numberOfVisiblePoints > maxChannelLength) {
    	AG_numberOfVisiblePoints = maxChannelLength;
    }
    targetVerticalLinePosition = AG_numberOfVisiblePoints * procentualLinePosition;
}

/**
 * Misc common startup logic. Part of AG startup
 * @private
 */
function _AG_preStart() {
    if (!isDoubleView) {
        var canvas = $('#EEGcanvasDiv');
		// Just use parent section width and height. For width remove some space for the labels to avoid scrolls
		// For height we have the toolbar there. Using 100% does not seem to work properly with FLOT.
    	canvas.width(canvas.parent().width() - 40);
    	canvas.height(canvas.parent().height() - 100);
    }
}

/**
 * Init selection component(s). Part of AG startup
 * @private
 */
function _AG_init_selection(filterGids){
    // create a selection component for each time series displayed by this eeg view
    var selectors = [];

    /** get all selected channels "idices" from all selector components */
    function getSelectedIndicesOfAllSelectors(){
        var all_selected = [];
        for(var selidx = 0; selidx < selectors.length; selidx++){
            all_selected = all_selected.concat( selectors[selidx].selectedIndices() );
        }
        return all_selected;
    }

    function getSelectedValuesOfAllSelectors(){
        var all_selected = [];
        for(var selidx = 0; selidx < selectors.length; selidx++){
            all_selected = all_selected.concat( selectors[selidx].val() );
        }
        return all_selected;
    }

    // init selectors
    for(var i = 0; i < filterGids.length; i++){
        var selectorId = "#channelSelector" + i;
        var selector = TVBUI.regionSelector(selectorId, {filterGid: filterGids[i]});
        selector.change(function(_current_selection){
            AG_submitableSelectedChannels = getSelectedValuesOfAllSelectors();
            refreshChannels();
        });
        selectors.push(selector);
    }
    // the first selector is special. we select by default some channels in it and in case of a dual view
    // his selection is synchronized with the brain
    AG_regionSelector = selectors[0];

    // If no values are selected the eeg view breaks! By default select the first channels of the first selector.
    // If there is any information stored in 'AG_submitableSelectedChannels' then the call to drawAnimatedChart.
    //came from a refrsh with a different page size. In this case there is no need to update the channel list.
    if (AG_submitableSelectedChannels.length == 0) {
        var defaultSelectionLength = Math.min(totalNumberOfChannels, DEFAULT_MAX_CHANNELS);
        // we take the values form the dom, a range(defaultSelectionLength) is not a valid selection if there are multiple time series
        AG_submitableSelectedChannels = AG_regionSelector._allValues.slice(0, defaultSelectionLength);
    }
    AG_regionSelector.val(AG_submitableSelectedChannels);
}

/**
 * Read speed from the dom
 * @param defaultSpeed default speed when there is no speed slider
 * @private
 */
function _AG_get_speed(defaultSpeed){
    var speed = defaultSpeed;
    if (!isSmallPreview  && !isDoubleView) {
    	speed = $("#ctrl-input-speed").slider("value");
    }
    return speed;
}

function AG_createYAxisDictionary(nr_channels) {
	/*
	 * Create FLOT specific options dictionary for the y axis, with correct labels and positioning for 
	 * all channels. Then store these values in 'AG_homeViewYValues' so they can be used in case of a 
	 * 'Home' action in a series of zoom events.
	 */
    var ticks, yaxis_dict, increment;

    if (AG_translationStep > 0) {
    	ticks = [];
        var step = AG_computedStep * AG_translationStep;
	    for (var i=0; i<nr_channels; i++) {
	    	ticks.push([i * step, chanDisplayLabels[displayedChannels[i]]]);
	    }
	    yaxis_dict = {
	    	min: - step,
	    	max: (nr_channels + 1) * step,
	    	ticks: ticks,
	    	zoomRange: [0.1, 20]
	    };
	    increment = nr_channels * step / numberOfPointsForVerticalLine;
        if(increment == 0) throw "infinite loop";
	    for (var k= -step; k < (nr_channels + 1) * step; k += increment) {
	    	followingLine.push([0, k]);
	    }
    }
    else {
    	ticks = [0, 'allChannels'];
	    yaxis_dict = {
	    	min: - AG_computedStep/2,
	    	max: AG_computedStep/2,
	    	ticks: ticks,
	    	zoomRange: [0.1, 20]
	    };
	    increment = AG_computedStep / numberOfPointsForVerticalLine;
        if(increment == 0) throw "infinite loop";
	    for (var kk= - AG_computedStep/2; kk < AG_computedStep/2; kk += increment) {
	    	followingLine.push([0, kk]);
	    }
    }
    AG_options.yaxis = yaxis_dict;
    AG_homeViewYValues = [yaxis_dict.min, yaxis_dict.max];
    AG_defaultYaxis = yaxis_dict;
}

function refreshChannels() {
	submitSelectedChannels(false); 
	drawGraph(false, noOfShiftedPoints);
}

function changeMode(selectComp) {
	var tsIndex = parseInt(selectComp.id.split('--'));
	tsModes[tsIndex] = parseInt($(selectComp).val());
	refreshChannels();
}

function changeStateVariable(selectComp) {
	var tsIndex = parseInt(selectComp.id.split('--'));
	tsStates[tsIndex] = parseInt($(selectComp).val());
	refreshChannels();
}


function submitSelectedChannels(isEndOfData) {
	/*
	 * Get required data for the channels in AG_submitableSelectedChannels. If none
	 * exist then just use the previous 'displayedChannels' (or default in case of first run).
	 */
    AG_currentIndex = AG_numberOfVisiblePoints;
    if (AG_submitableSelectedChannels.length == 0) {
        AG_submitableSelectedChannels = displayedChannels.slice();
    }

    if (!(isEndOfData && maxDataFileIndex == 0)) {
        AG_allPoints = [];
        displayedChannels = AG_submitableSelectedChannels.slice(0); // todo: dubious as displayedChannels seems to store indices not values
        generateChannelColors(displayedChannels.length);
		
		var offset = 0;
        var channelLengths = [];
        for (var i = 0; i < nrOfPagesSet.length; i++) {
        	var dataURL = readDataPageURL(baseDataURLS[i], 0, dataPageSize, tsStates[i], tsModes[i]);
            var data = HLPR_readJSONfromFile(dataURL);
            var result = parseData(data, i);
            var selectedChannels = getDisplayedChannels(result, offset);
            offset = offset + result.length;
            // todo: duplicated in this file
            if (selectedChannels.length > 0) {
            	channelLengths.push(selectedChannels[0].length);
            } else {
            	channelLengths.push(-1);
            }
            AG_allPoints = AG_allPoints.concat(selectedChannels);
        }
        // keep data only for the selected channels
        AG_noOfLines = AG_allPoints.length;
        longestChannelIndex = channelLengths.indexOf(Math.max.apply(Math, channelLengths));
    }
    
    AG_displayedPoints = [];
    AG_displayedTimes = [];
    for (var ii = 0; ii < AG_noOfLines; ii++) {
        AG_displayedPoints.push([]);
    }

    if (!(isEndOfData && maxDataFileIndex == 0)) {
        //read time
        readTimeData(0, false);
        AG_time = nextTimeData.slice(0);
    }
    // reset data
    nextData = [];
    nextTimeData = [];
    AG_isLoadStarted = false;
    isNextDataLoaded = false;
    isNextTimeDataLoaded = false;
    currentDataFileIndex = 0;
    totalPassedData = 0;
    currentLinePosition = 0;
    if (nanValueFound) {
        displayMessage('The given data contains some NaN values. All the NaN values were replaced by zero.','warningMessage')
    }

    // draw the first 'AG_numberOfVisiblePoints' points
    redrawCurrentView();
    if (isSmallPreview == false) {
    	AG_translationStep = $('#ctrl-input-scale').slider("option", "value") / 4;
    } else {
    	AG_translationStep = 1;
    }
    

    AG_createYAxisDictionary(AG_noOfLines);
    redrawPlot([]);
    resetToDefaultView();
    if (AG_isStopped ) {
    	AG_isStopped = false;
        drawGraph(false, noOfShiftedPoints);
        AG_isStopped = true;
    } else {
    	drawGraph(false, noOfShiftedPoints);
    }
}

/**
 * This method decides if we are at the beginning or end of the graph, in which case we only need
 * to move the vertical line, or in between, where vertical line is not moving, instead arrays are shifted.
 */
function shouldMoveLine(direction, shiftNo) {
	shiftNo = shiftNo || 1;
	var isEndOfGraph = false;
	var isStartOfGraph = false;
	if (direction == 1) {
		isEndOfGraph = ((totalPassedData + AG_currentIndex + noOfShiftedPoints >= totalTimeLength) && (currentLinePosition < AG_numberOfVisiblePoints + shiftNo));	
		isStartOfGraph = (currentLinePosition < targetVerticalLinePosition);		
		if (AG_displayedTimes[currentLinePosition] > AG_displayedPoints[longestChannelIndex][AG_displayedPoints[longestChannelIndex].length - 1][0]) {
	    	isEndOfGraph = false;
	    }
	} else {
		isEndOfGraph = (currentLinePosition > targetVerticalLinePosition);
		isStartOfGraph = ((totalPassedData + AG_currentIndex - noOfShiftedPoints < AG_numberOfVisiblePoints) && (currentLinePosition > 0));
		if (AG_displayedTimes[currentLinePosition] <= 0) {
	    	isStartOfGraph = false;
	    }
	}
	
	return isStartOfGraph || isEndOfGraph;
}

var isEndOfData = false;
var AG_channelColorsDict = {};
var AG_reversedChannelColorsDict = {};

function generateChannelColors(nr_of_channels) {
	/*
	 * Generate different colors for each channel.
	 */
	AG_channelColorsDict = {};
	AG_reversedChannelColorsDict = {};
	var step = parseInt(255 / nr_of_channels);
	for (var i=0; i<nr_of_channels; i++) {
		var color = "rgb("+255*(i%2)+","+(255-i*step)+","+255*((i+1)%2)+")";
		AG_channelColorsDict[color] = i;
		AG_reversedChannelColorsDict[i] = color; 
	}
}


function setLabelColors() {
	/*
	 * Get x-axis labels and update colors to correspond to each channel
	 */
	var labels = $('.tickLabel');
	for (var i=0; i<labels.length; i++) {
		var chan_idx = chanDisplayLabels.indexOf(labels[i].firstChild.textContent);
		if (chan_idx >= 0) {
			labels[i].style.color = AG_reversedChannelColorsDict[displayedChannels.indexOf(chan_idx)];
			labels[i].style.width = '100px';
		}
	}
}


function drawGraph(executeShift, shiftNo) {
	/*
	 * This method draw the actual plot. The 'executeShift' parameter decides if a shift is
	 * to be done, or just use the previous data points. 'shiftNo' decides the number of points
	 * that will be shifted.
	 */
	noOfShiftedPoints = shiftNo;
	if (isEndOfData) {
		isEndOfData = false;
    	submitSelectedChannels(true);
    }
    if (t != null) {
        clearTimeout(t);
    }
    if (AG_isStopped) {
        return;
    }
    if (shouldLoadNextDataFile()) {
        loadNextDataFile();
    }

	var direction = 1;

    if (_AG_get_speed(1) < 0){
        direction = -1;
	}
	
	var moveLine = shouldMoveLine(direction, noOfShiftedPoints);
	//Increment line position in case we need to move the line
	if (moveLine && executeShift && !AG_isSpeedZero) {
	    currentLinePosition = currentLinePosition + noOfShiftedPoints * direction;	
    }

    if (currentLinePosition >= AG_numberOfVisiblePoints) {
        isEndOfData = true;
    }

    if (executeShift && !AG_isSpeedZero && !moveLine) {
        var count = 0;
        if (direction == -1) {
            if (currentDataFileIndex > 0 || AG_currentIndex > AG_numberOfVisiblePoints) {
                count = 0;
                while (count < noOfShiftedPoints && AG_currentIndex - count > AG_numberOfVisiblePoints) {
                    count = count + 1;
                	AG_displayedTimes.unshift(AG_time[AG_currentIndex - AG_numberOfVisiblePoints - count]);
                    for (i = 0; i < AG_displayedPoints.length; i++) {
                        AG_displayedPoints[i].unshift(
                                [   AG_time[AG_currentIndex - AG_numberOfVisiblePoints - count],
                                    AG_addTranslationStep(AG_allPoints[i][AG_currentIndex - AG_numberOfVisiblePoints - count], i)
                                ]);
                        AG_displayedPoints[i].pop();
                    }
                	AG_displayedTimes.pop();
                }

                if (AG_currentIndex - count > AG_numberOfVisiblePoints) {
                    AG_currentIndex = AG_currentIndex - count;
                } else {
                    AG_currentIndex = Math.min(AG_currentIndex, AG_numberOfVisiblePoints);
                    if (currentDataFileIndex > 0 && isNextDataLoaded) {
                        changeCurrentDataFile();
                    }
                }
            }
        } else {
            if (totalTimeLength > AG_currentIndex + totalPassedData) {
                // here we add new 'noOfShiftedPoints' points to the chart and remove the first 'noOfShiftedPoints' visible points
                count = 0;
                while (count < noOfShiftedPoints && totalTimeLength > AG_currentIndex + count) {
                	AG_displayedTimes.push(AG_time[AG_currentIndex + count]);
                    for (i = 0; i < AG_displayedPoints.length; i++) {
                        AG_displayedPoints[i].push(
                                [   AG_time[AG_currentIndex + count],
                                    AG_addTranslationStep(AG_allPoints[i][AG_currentIndex + count], i)
                                 ]);
                        AG_displayedPoints[i].shift();
                    }
                    AG_displayedTimes.shift();
                    count = count + 1;
                }

                if (AG_currentIndex + count < AG_allPoints[longestChannelIndex].length) {
                    AG_currentIndex = AG_currentIndex + count;
                } else {
                    AG_currentIndex = Math.max(AG_currentIndex, AG_allPoints[longestChannelIndex].length);
                    if (maxDataFileIndex > 0 && isNextDataLoaded) {
                        changeCurrentDataFile();
                    }
                }
            }
        }
    }
    if (!AG_isSpeedZero) {
    	for (var i=0; i<followingLine.length; i++) {
    		followingLine[i][0] = AG_displayedTimes[currentLinePosition]
    	}
	    var preparedData = [];
	    for (var j = 0; j < AG_displayedPoints.length; j++) {
	    	preparedData.push({data: AG_displayedPoints[j].slice(0), color: AG_reversedChannelColorsDict[j]});
	    }
	    preparedData.push({data: followingLine, color: 'rgb(255, 0, 0)'});
		plot.setData(preparedData);
		plot.setupGrid();
		plot.draw();
		setLabelColors();
    }
    if (!isDoubleView) {
    	t = setTimeout("drawGraph(true, noOfShiftedPoints)", getTimeoutBasedOnSpeed());
    }
}

function redrawPlot(data) {
	/*
	 * Do a redraw of the plot. Be sure to keep the resizable margin elements as the plot method seems to destroy them.
	 */
    var target = $('#EEGcanvasDiv');
    var resizerChildren = target.children('.ui-resizable-handle');
    for (var i=0; i < resizerChildren.length; i++) {
    	target[0].removeChild(resizerChildren[i]);
    }
    plot = $.plot(target, data, $.extend(true, {}, AG_options));
    for (var j=0; j < resizerChildren.length; j++) {
    	target[0].appendChild(resizerChildren[j]);
    }
    setLabelColors();
}


/**
 * This hook will be called before Flot copies and normalizes the raw data for the given
 * series. If the function fills in datapoints.points with normalized
 * points and sets datapoints.pointsize to the size of the points,
 * Flot will skip the copying/normalization step for this series.
 */
function processRawDataHook(plot, series, data, datapoints) {
    datapoints.format = [
        { x: true, number: true, required: true },
        { y: true, number: true, required: true }
    ];
    datapoints.pointsize = 2;

    for (var i = 0; i < data.length; i++) {
        datapoints.points.push(data[i][0]);
        datapoints.points.push(data[i][1]);
    }

    series.xaxis.used = series.yaxis.used = true;
}


/**
 * Translate the given value.
 * We use this method to translate the values for the drawn line charts because we don't want them to overlap.
 *
 * @param value the value that should be translated.
 * @param index the number of <code>AG_translationSteps</code> that should be used for translating the given value.
 * @return {number}
 */
function AG_addTranslationStep(value, index) {
    return value - AG_normalizationSteps[displayedChannels[index]] + AG_translationStep * AG_computedStep * index;
}

function getTimeoutBasedOnSpeed() {
    var currentAnimationSpeedValue = _AG_get_speed(40);

    if (currentAnimationSpeedValue == 0) {
        return 300;
    }
    var timeout = 10 - Math.abs(currentAnimationSpeedValue);
    if (timeout == 9) {
        return 3000;
    }
    if (timeout == 8) {
        return 2000;
    }
    if (timeout == 7) {
        return 1000;
    }
    return timeout * 100 + 25;
}


function loadEEGChartFromTimeStep(step) {
	/*
	 * Load the data from a given step and center plot around that step.
	 */
	// Read all data for the page in which the selected step falls into
	var chunkForStep = Math.floor(step / dataPageSize);
	var dataUrl = readDataPageURL(baseDataURLS[0], chunkForStep * dataPageSize, (chunkForStep + 1) * dataPageSize, tsStates[0], tsModes[0]);
	var dataPage = [parseData(HLPR_readJSONfromFile(dataUrl), 0)];
    AG_allPoints = getDisplayedChannels(dataPage[0], 0).slice(0);
	AG_time = HLPR_readJSONfromFile(timeSetUrls[0][chunkForStep]).slice(0);
	
	totalPassedData = chunkForStep * dataPageSize;	// New passed data will be all data until the start of this page
	currentDataFileIndex = chunkForStep;
    AG_displayedPoints = [];
	var indexInPage = step % dataPageSize;	// This is the index in the current page that step will have
	var fromIdx, toIdx;
	currentLinePosition = AG_numberOfVisiblePoints / 2; // Assume we are not end or beginning since that will be most of the times
	if (indexInPage <= AG_numberOfVisiblePoints / 2) {
		if (chunkForStep == 0) {
			// We are at the beginning of the graph, line did not reach middle point yet, and we are still displaying the first
			// AG_numberOfVisiblePoints values
			AG_currentIndex = AG_numberOfVisiblePoints;
			currentLinePosition = indexInPage;
			prepareDisplayData(0, AG_numberOfVisiblePoints, AG_allPoints, AG_time);
		} else {
			// We are at an edge case between pages. So in order to have all the 
			// AG_numberOfVisiblePoints we need to also load the points from before this page
			addFromPreviousPage(indexInPage, chunkForStep);
		}
	} else {
		if ((indexInPage >= pageSize - AG_numberOfVisiblePoints / 2) || (nrOfPagesSet[0] == 1 && indexInPage + AG_numberOfVisiblePoints / 2 > AG_time.length)) {
			if (chunkForStep >= nrOfPagesSet[0] - 1) {
				// We are at the end of the graph. The line is starting to move further right from the middle position. We are just
				// displaying the last AG_numberOfVisiblePoints from the last page
				if (AG_time.length > AG_numberOfVisiblePoints) {
					fromIdx = AG_time.length - 1 - AG_numberOfVisiblePoints;
				} else {
					fromIdx = 0;
				}
				toIdx = AG_time.length - 1;
				AG_currentIndex = toIdx;
				currentLinePosition = AG_numberOfVisiblePoints - (AG_time.length - 1 - indexInPage); 
				prepareDisplayData(fromIdx, toIdx, AG_allPoints, AG_time);
			} else {
				// We are at an edge case between pages. So in order to have all the 
				// AG_numberOfVisiblePoints we need to also load the points from after this page
				addFromNextPage(indexInPage, chunkForStep);
			}
		} else {
 				// We are somewhere in the middle of the graph. 
				fromIdx = indexInPage - AG_numberOfVisiblePoints / 2;
				toIdx = indexInPage + AG_numberOfVisiblePoints / 2;
				AG_currentIndex = toIdx;
				prepareDisplayData(fromIdx, toIdx, AG_allPoints, AG_time);
			}
	} 
	nextData = [];
    AG_isLoadStarted = false;
    isNextDataLoaded = false;
    isNextTimeDataLoaded = false;
}


function addFromPreviousPage(indexInPage, currentPage) {
	/*
	 * Add all required data to AG_displayedPoints and AG_displayedTimes in order to center
	 * around indexInPage, if some of the required data is on the previous page.
	 */
	var previousPageUrl = readDataPageURL(baseDataURLS[0], (currentPage - 1) * dataPageSize, currentPage * dataPageSize, tsStates[0], tsModes[0]);
	var previousData = parseData(HLPR_readJSONfromFile(previousPageUrl), 0);
	previousData = getDisplayedChannels(previousData, 0).slice(0);
	var previousTimeData = HLPR_readJSONfromFile(timeSetUrls[0][currentPage - 1]);
	// Compute which slices we would need from the 'full' two-pages data.
	// We only need the difference so to center indexInPage at AG_numberOfVisiblePoints / 2
    var fromIdx, toIdx;
	fromIdx = previousData[0].length - (AG_numberOfVisiblePoints / 2 - indexInPage);  // This is from where we need to read from previous data
	AG_currentIndex = toIdx = AG_numberOfVisiblePoints - (AG_numberOfVisiblePoints / 2 - indexInPage); // This is where we need to add from the current page
	// Just generate displayed point and displayed times now
	for (var idx = 0; idx < previousData.length; idx++) {
			var oneLine = [];
			// Push data that is from previos slice
			for (var idy = fromIdx; idy < previousData[0].length; idy++) {
				oneLine.push([previousTimeData[idy], AG_addTranslationStep(previousData[idx][idy], idx)])
			}
			// Now that that is from our current slice
			for (idy = 0; idy < toIdx; idy ++) {
				oneLine.push([AG_time[idy], AG_addTranslationStep(AG_allPoints[idx][idy], idx)])
			}
			AG_displayedPoints.push(oneLine);
		}
	AG_displayedTimes = previousTimeData.slice(fromIdx).concat(AG_time.slice(0, toIdx));
	previousData = null;
}


function addFromNextPage(indexInPage, currentPage) {
	/*
	 * Add all required data to AG_displayedPoints and AG_displayedTimes in order to center
	 * around indexInPage, if some of the required data is on the next page.
	 */
	var followingPageUrl = readDataPageURL(baseDataURLS[0], (currentPage + 1) * dataPageSize, (currentPage + 2) * dataPageSize, tsStates[0], tsModes[0]);
	var followingData = parseData(HLPR_readJSONfromFile(followingPageUrl), 0);
	followingData = getDisplayedChannels(followingData, 0).slice(0);
	var followingTimeData = HLPR_readJSONfromFile(timeSetUrls[0][currentPage + 1]);
	var fromIdx, toIdx;
	fromIdx = indexInPage - (AG_numberOfVisiblePoints / 2);	// We need to read starting from here from the current page
	AG_currentIndex = toIdx = fromIdx + AG_numberOfVisiblePoints - AG_allPoints[0].length;	// We need to read up to here from next page
	for (var idx = 0; idx < AG_allPoints.length; idx++) {
		var oneLine = [];
		// Push data that is from this slice
		for (var idy = fromIdx; idy < AG_allPoints[0].length; idy++) {
			oneLine.push([AG_time[idy], AG_addTranslationStep(AG_allPoints[idx][idy], idx) ])
		}
		// Now that that is from next slice
		for (idy = 0; idy < toIdx; idy ++) {
			oneLine.push([followingTimeData[idy], AG_addTranslationStep(followingData[idx][idy], idx) ])
		}
		AG_displayedPoints.push(oneLine);
	}
	AG_displayedTimes = AG_time.slice(fromIdx).concat(followingTimeData.slice(0, toIdx));
	// Since next page is already loaded, that becomes the current page
	AG_allPoints = followingData;
	AG_time = followingTimeData;
	totalPassedData = (currentPage + 1) * dataPageSize;
	currentDataFileIndex = currentPage + 1;
	isNextDataLoaded = true;
	isNextTimeDataLoaded = true;
}


function prepareDisplayData(fromIdx, toIdx, pointsArray, timeArray) {
	/*
	 * Just re-populate whole displayedPoints and displayedTimes given a start and end index.
	 */
	for (var idx = 0; idx < pointsArray.length; idx++) {
		var oneLine = [];
		for (var idy = fromIdx; idy < toIdx; idy++) {
			oneLine.push([ timeArray[idy], AG_addTranslationStep(pointsArray[idx][idy], idx) ])
		}
		AG_displayedPoints.push(oneLine);
	}
	AG_displayedTimes = timeArray.slice(fromIdx, toIdx)
}


function loadNextDataFile() {
	/*
	 * Read the next data file asyncronously. Also get the corresponding time data file.
	 */
    AG_isLoadStarted = true;
    var nx_idx = getNextDataFileIndex();
    cachedFileIndex = nx_idx;
    AG_readFileDataAsynchronous(nrOfPagesSet, noOfChannelsPerSet, nx_idx, maxChannelLength, 0);
    readTimeData(nx_idx, true);
}

function changeCurrentDataFile() {
    if (!isNextDataLoaded || !isNextTimeDataLoaded) {
        return;
    }

    if (cachedFileIndex != getNextDataFileIndex()) {
        AG_isLoadStarted = false;
        isNextDataLoaded = false;
        isNextTimeDataLoaded = false;
        nextData = [];
        nextTimeData = [];
        return;
    }

    var speed = _AG_get_speed(100);
    var longestChannelLength = AG_allPoints[longestChannelIndex].length;

    if (speed > 0) {
        totalPassedData = totalPassedData + longestChannelLength;
        if (longestChannelLength < AG_currentIndex) {
            AG_currentIndex = - (longestChannelLength - AG_currentIndex);
        } else {
            AG_currentIndex = 0;
        }
    } else if (speed < 0) {
        totalPassedData = totalPassedData - longestChannelLength;
        if (totalPassedData < 0) {
            totalPassedData = 0;
        }
    } else {
        return;
    }

    AG_allPoints = nextData.slice(0);
    nextData = [];
    AG_time = nextTimeData.slice(0);
    nextTimeData = [];
    currentDataFileIndex = getNextDataFileIndex();
    AG_isLoadStarted = false;
    isNextDataLoaded = false;
    isNextTimeDataLoaded = false;

    if (speed < 0) {
        AG_currentIndex = longestChannelLength + AG_currentIndex;
    }
}

function shouldLoadNextDataFile() {
    if (!AG_isLoadStarted && maxDataFileIndex > 0) {
        var nextFileIndex = getNextDataFileIndex();
        var speed = _AG_get_speed(1); // Assume left to right pass of data

        if ((speed > 0) && (currentDataFileIndex != nextFileIndex) && (maxChannelLength - AG_currentIndex < threshold * AG_numberOfVisiblePoints)) {
            return true;
        } 
        if ((speed < 0) && (currentDataFileIndex != nextFileIndex) && (AG_currentIndex-AG_numberOfVisiblePoints < threshold * AG_numberOfVisiblePoints)) {
            return true;
        }
    }
    return false;
}

function setMaxDataFileIndex(nrOfPagesPerArray) {
	/*
	 * In case of multiple arrays find out which has the most data files that need
	 * to be loaded.
	 */
    var max_ln = 0;
    for (var i = 0; i < nrOfPagesPerArray.length; i++) {
        if (nrOfPagesPerArray[i] > max_ln) {
            max_ln = nrOfPagesPerArray[i];
        }
    }
    maxDataFileIndex = max_ln - 1;
}

function getNextDataFileIndex() {
	/*
	 * Return the index of the next data file that should be loaded.
	 */
    var nextIndex;
	var speed = _AG_get_speed(100);
    if (speed > 0) {
        nextIndex = currentDataFileIndex + 1;
        if (nextIndex >= maxDataFileIndex) {
            return maxDataFileIndex;
        }
    } else {
        nextIndex = currentDataFileIndex - 1;
        if (nextIndex <= 0) {
            return 0;
        }
    }
    return nextIndex;
}

function AG_readFileDataAsynchronous(nrOfPages, noOfChannelsPerSet, currentFileIndex, maxChannelLength, dataSetIndex) {
    if (dataSetIndex >= nrOfPages.length) {
        isNextDataLoaded = true;
        // keep data only for the selected channels
        var offset = 0;  // fixme: this is used in getDisplayedChannels to offset the channel indices. but indices might not start at 0
        // fixme: there is a confusion of indices with chanel id's (numeric values)
        var selectedData = [];
        var channelLengths = [];
        for (var i = 0; i< nextData.length; i++) {
        	var selectedChannels = getDisplayedChannels(nextData[i], offset);
            offset = offset + nextData[i].length;
            if (selectedChannels.length > 0) {
            	channelLengths.push(selectedChannels[0].length);
            } else {
            	channelLengths.push(-1);
            }
            selectedData = selectedData.concat(selectedChannels);
        }
        longestChannelIndex = channelLengths.indexOf(Math.max.apply(Math, channelLengths));
        nextData = selectedData;
        return;
    }
    if (nrOfPages[dataSetIndex] - 1 < currentFileIndex && AG_isLoadStarted) {
        // todo: assumed that this is computing a padding for smaller signals. check if this is really the purpose of this
        var padding = [];
        var oneChannel = [];
        for (var j = 0; j < maxChannelLength; j++) {
            oneChannel.push(0);
        }
        for (j = 0; j < noOfChannelsPerSet[dataSetIndex]; j++) {
            padding.push(oneChannel);
        }
        nextData.push(padding);

        AG_readFileDataAsynchronous(nrOfPages, noOfChannelsPerSet, currentFileIndex, maxChannelLength, dataSetIndex + 1);
    } else {
        doAjaxCall({
            url: readDataPageURL(baseDataURLS[dataSetIndex], currentFileIndex * dataPageSize, (currentFileIndex + 1) * dataPageSize, tsStates[dataSetIndex], tsModes[dataSetIndex]),
            success: function(data) {
            	if (AG_isLoadStarted) {
            		data = $.parseJSON(data);
	                var result = parseData(data, dataSetIndex);
	                // nextData = nextData.concat(result);
	                nextData.push(result);
	
	                AG_readFileDataAsynchronous(nrOfPages, noOfChannelsPerSet, currentFileIndex, maxChannelLength, dataSetIndex + 1);
            	}
            }
        });
    }
}

function parseData(dataArray, dataSetIndex) {
	/*
	 * Data is recieved from the HLPR_parseJSON as a 500/74 array. We need to transform it
	 * into an 74/500 one and in the transformation also replace all NaN values.
	 */
    var result = [];
    for (var i = 0; i < noOfChannelsPerSet[dataSetIndex]; i++) {
    	result.push([])
    }
    for (var j = 0; j < dataArray.length; j++) {
    	for (var k = 0; k < noOfChannelsPerSet[dataSetIndex]; k++) {
    		var arrElem = dataArray[j][k];
    		if (arrElem == 'NaN') {
    			nanValueFound = true;
    			arrElem = 0;
    		}
    		result[k].push(arrElem)
    	}
    }
    return result;
}

/**
 *
 * @param fileIndex
 * @param asyncRead <code>true</code> only if the file should be read asynchronous
 */
function readTimeData(fileIndex, asyncRead) {
    if (timeSetUrls[longestChannelIndex].length <= fileIndex) {
        nextTimeData = [];
        for (var i = 0; i < maxChannelLength; i++) {
            nextTimeData.push(totalPassedData + i);
        }
        isNextTimeDataLoaded = true;
    } else {
        if (asyncRead) {
            doAjaxCall({
                url: timeSetUrls[longestChannelIndex][fileIndex],
                success: function(data) {
                    nextTimeData = $.parseJSON(data);
                    isNextTimeDataLoaded = true;
                }
            });
        } else {
            nextTimeData = HLPR_readJSONfromFile(timeSetUrls[longestChannelIndex][fileIndex]);
            isNextTimeDataLoaded = true;
        }
    }
}

function getArrayFromDataFile(dataFile) {
    var fileData = dataFile.replace(/\n/g, " ").replace(/\t/g, " ");
    var arrayData = $.trim(fileData).split(" ");
    for (var i = 0; i < arrayData.length; i++) {
        arrayData[i] = parseFloat(arrayData[i]);
    }
    return arrayData;
}

function getDisplayedChannels(listOfAllChannels, offset) {
    var selectedData = [];
    for (var i = 0; i < displayedChannels.length; i++) {
    	if (listOfAllChannels[displayedChannels[i] - offset] != undefined)
        	selectedData.push(listOfAllChannels[displayedChannels[i] - offset].slice(0));
    }
    return selectedData;
}
