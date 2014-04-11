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

/*
 * ---------------------------------------===========================================--------------------------------------
 * WARNING: This script is just adding some functionality specific to the stimulus on top of what is defined 
 * in /static/js/spatial/base_spatial.js. As such in all the cases when this script is used, you must first 
 * include base_spatial.js. In case you need to ADD FUNCTIONS here, either make sure you don't "overwrite" something
 * necessary from base_spatial.js, or just prefix your functions. (e.g. STIM_SPATIAL_${function_name}).
 * ---------------------------------------===========================================--------------------------------------
 */

// the default weights values for a region stimulus; needed for reset action
var originalRegionStimulusWeights = [];
// the updated weights values for a region stimulus
var updatedRegionStimulusWeights = [];
var SEL_selector;

function STIM_initSelectionComponent(selectionGID){
    SEL_selector = TVBUI.textGridRegionSelector("#channelSelector", {filterGid: selectionGID});
    TVBUI.quickSelector(SEL_selector, "#selection-text-area", "#loadSelectionFromTextBtn");

    SEL_selector.change(function(value){
        GVAR_interestAreaNodeIndexes = [];
        for(var i=0; i < value.length; i++){
            GVAR_interestAreaNodeIndexes.push(parseInt(value[i], 10));
        }
    });

    SEL_selector.setGridText(updatedRegionStimulusWeights);
    SEL_selector.checkAll();
}

/**
 * Method used for making initializations.
 */
function STIM_initConnectivityViewer(weights) {
        //The click event is bound on the div in which will be placed the connectivity canvas.
        //If I bind the event on the canvas and I'll change the connectivity which in turn
        // will change the canvas => on the new canvas the click event won't be bound
        $('#GLcanvas').unbind('click.toggleNodeSelection').bind('click.toggleNodeSelection', function (e) {
            if (e.target == document.getElementById("GLcanvas")) {
                STIM_toggleNodeSelection(CONN_pickedIndex);
            }
        });
        originalRegionStimulusWeights = weights;
        updatedRegionStimulusWeights = originalRegionStimulusWeights.slice(0);
        GVAR_connectivityNodesWithPositiveWeight = [];
}

function _STIM_server_update_scaling(){
    doAjaxCall({
        async: false,
        type: 'POST',
        data: {'scaling' : JSON.stringify(updatedRegionStimulusWeights)},
        url:'/spatial/stimulus/region/update_scaling'
    });
}

/**
 * Saves the given weight for all the selected nodes.
 */
function STIM_saveWeightForSelectedNodes() {
    var weightElement = $("#current_weight");
    var newWeight = parseFloat(weightElement.val());
    if (!isNaN(newWeight)) {
        for (var i = 0; i < GVAR_interestAreaNodeIndexes.length; i++) {
            var nodeIndex = GVAR_interestAreaNodeIndexes[i];
            updatedRegionStimulusWeights[nodeIndex] = newWeight;
        }
        weightElement.val("");
        SEL_selector.setTextForSelection(newWeight);
        SEL_selector.clearAll();
        _STIM_server_update_scaling();
    }
}


/**
 * Resets all the weights to their default values.
 */
function STIM_resetRegionStimulusWeights() {
    updatedRegionStimulusWeights = originalRegionStimulusWeights.slice(0);
    SEL_selector.setGridText(updatedRegionStimulusWeights);
    _STIM_server_update_scaling();
}


/**
 * Toggle the selection of the given node.
 *
 * @param nodeIndex the index of the selected node.
 */
function STIM_toggleNodeSelection(nodeIndex) {
    if (nodeIndex >= 0) {
        GFUNC_toggleNodeInInterestArea(nodeIndex);
        SEL_selector.val(GVAR_interestAreaNodeIndexes);
    }
}


/**
 * Submits all the region stimulus data to the server for creating a new Stimulus instance.
 *
 * @param actionUrl the url at which will be submitted the data.
 * @param nextStep
 * @param checkScaling
 */
function STIM_submitRegionStimulusData(actionUrl, nextStep, checkScaling) {
	if (checkScaling) {
		var scalingSet = false;
		for (var i=0; i<updatedRegionStimulusWeights.length; i++) {
			if (updatedRegionStimulusWeights[i] != 0) {
				scalingSet = true;
			}
		}
		if ( !scalingSet ) {
			displayMessage("You should set scaling that is not 0 for at least some nodes.", "warningMessage");
        	return;
		}
	}
	_submitPageData(actionUrl, {'next_step' : nextStep})
}


/**
 * *******************************************  *******************************************
 * CODE FOR SURFACE STIMULUS STARTING HERE.....
 * *******************************************  *******************************************
 */

/*
 * NOTE: The method is called through eval. Do not remove it.
 *
 * Parse the entry for the focal points and load them into js to be later used.
 */
function STIM_initFocalPoints(focal_points) {
	for (var i = 0; i < focal_points.length; i++) {
		var focalPoint = parseInt(focal_points[i]);
		BS_addedFocalPointsTriangles.push(focalPoint);
		BS_addedSurfaceFocalPoints.push(focalPoint);
		TRIANGLE_pickedIndex = focalPoint;
		BASE_PICK_moveBrainNavigator(true);
		BASE_PICK_addFocalPoint(focalPoint);
	}
	BS_drawSurfaceFocalPoints();
}


/*
 * Remove all previously defined focal points.
 */
function STIM_deleteAllFocalPoints() {
	for (var i = BS_addedFocalPointsTriangles.length - 1; i >= 0; i--) {
		BS_removeFocalPoint(i);
	}
}


/**
 * Collects the data needed for creating a SurfaceStimulus and submit it to the server.
 *
 * @param actionUrl the url at which will be submitted the data.
 * @param nextStep
 * @param includeFocalPoints
 */
function STIM_submitSurfaceStimulusData(actionUrl, nextStep, includeFocalPoints) {
    if (includeFocalPoints && BS_addedSurfaceFocalPoints.length < 1) {
        displayMessage("You should define at least one focal point.", "errorMessage");
        return;
    }
    var baseDict = {'next_step' : nextStep};
	if (includeFocalPoints) {
		baseDict['defined_focal_points'] = JSON.stringify(BS_addedFocalPointsTriangles);
	}
    _submitPageData(actionUrl, baseDict)
}


/*
 * Gather the data from all the forms in the page and submit them to actionUrl.
 *
 * @param actionUrl: the url to which data will be submitted
 * @param baseData:
 */
function _submitPageData(actionUrl, baseData) {
	var pageForms = $('form');
	for (var i=0; i<pageForms.length; i++) {
		pageForms[i].id = "form_id_" + i;
		var formData = getSubmitableData(pageForms[i].id, false);
		for (key in formData) {
			baseData[key] = formData[key];
		}
	}

    var parametersForm = document.createElement("form");
    parametersForm.method = "POST";
    parametersForm.action = actionUrl;
    document.body.appendChild(parametersForm);

    for (var key in baseData) {
        var input = document.createElement('INPUT');
        input.type = 'hidden';
        input.name = key;
        input.value = baseData[key];
        parametersForm.appendChild(input);
    }

    parametersForm.submit();
}