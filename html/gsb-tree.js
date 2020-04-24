var idToPoint = {};
var selectedSegments = [];
var board = null;

let options = {
	//color: '#42A5F5',
	//hl_color: '#00E6E3',
	color: '#222222',
	hl_color: '#F44336',
};

function initScene(l, t, r, b) {
	board = JXG.JSXGraph.initBoard('scene', {
		boundingbox: [l, t, r, b],
		keepaspectratio: true,
		showNavigation: false,
		showCopyright: false,
		registerEvents: false
	});
}

function addPoint(name, x, y) {
	idToPoint[name] = board.create('point', [x, y], {
		name: name,
		id: name,
		color: options.color,
		highlightFillColor: options.hl_color,
		highlightStrokeColor: options.hl_color,
		size: 3,
		label: {color: options.color, offset: [20, 6]}
	});
}

function addLine(pt0, pt1) {
	board.create('line', [idToPoint[pt0], idToPoint[pt1]], {
		straightFirst: false,
		straightLast: false,
		strokeWidth: 0.7,
		color: options.color
	});
}

function setupTree() {
	var root = document.getElementById('gsb-tree');
	root.querySelectorAll('span').forEach(item => {
		if (item.parentElement.nodeName.toLowerCase() == 'span') {
			return;
		}
		item.classList.forEach(cls => {
			var points = null;
			var lines = [];
			if (cls.startsWith('tr__')) {
				points = cls.split('__').slice(1, 4);
				lines = [
					{s: points[0], e: points[1]},
					{s: points[0], e: points[2]},
					{s: points[1], e: points[2]}
				];
			} else if (cls.startsWith('ang__')) {
				points = cls.split('__').slice(1, 4);
				lines = [
					{s: points[1], e: points[0], type: 'ray'},
					{s: points[1], e: points[2], type: 'ray'}
				];
			} else if (cls.startsWith('vec__')) {
				points = cls.split('__').slice(1, 3);
				lines = [{s: points[0], e: points[1]}];
			} else if (cls.startsWith('ray__')) {
				points = cls.split('__').slice(1, 3);
				lines = [{s: points[0], e: points[1], type: 'ray'}];
			} else if (cls.startsWith('seg__')) {
				points = cls.split('__').slice(1, 3);
				lines = [{s: points[0], e: points[1]}];
			} else if (cls.startsWith('pt__')) {
				points = cls.split('__').slice(1, 2);
			}
			if (points) {
				item.addEventListener('mouseover', function() {
					points.forEach(id => { idToPoint[id].highlight(); });
					lines.forEach(ln => {
						selectedSegments.push(board.create(
							'line', [idToPoint[ln['s']], idToPoint[ln['e']]], {
								straightFirst: false,
								straightLast: ln['type'] == 'ray',
								color:options.hl_color,
								strokeWidth:1.0
							})
						);
					});
					root.querySelectorAll('.' + cls).forEach(elt => {elt.style.background = options.hl_color;});
				});
				item.addEventListener('mouseleave', function() {
					points.forEach(id => { idToPoint[id].noHighlight(); });
					selectedSegments.forEach(obj => {board.removeObject(obj);});
					root.querySelectorAll('.' + cls).forEach(elt => {elt.style.background = null;});
				});
			}
		});
	});
	root.querySelectorAll('li').forEach(item => {
		if (item.querySelector('ul') == null) {
			return;
		}
		item.classList.add('closed');
		item.classList.remove('open');
		item.addEventListener('click', function(e) {
			this.classList.toggle('open');
			this.classList.toggle('closed');
			e.stopPropagation();
		});
	});
}

function toggleNonEssential() {
	var root = document.getElementById('gsb-tree');
	var props = root.querySelectorAll('.normal');
	if (root.querySelector('#checkbox').checked) {
		props.forEach(item => { item.style.display='block'; });
	} else {
		props.forEach(item => { item.style.display='none'; });
	}
	root.querySelectorAll('li').forEach(item => {
		var list = item.querySelector('ul');
		if (list == null) {
			return;
		}
		var hasVisibleChildren = false;
		for (i = 0; i < list.children.length; i++) {
			if (list.children[i].style.display != 'none') {
				hasVisibleChildren = true;
				break;
			}
		}
		if (!hasVisibleChildren) {
			item.classList.add('empty');
		} else {
			item.classList.remove('empty');
		}
	});
};

function adjustSceneLabels() {
	Object.keys(idToPoint).forEach(id => {
		var label = document.querySelector('#scene_' + id + 'Label');
		label.style.left = (parseFloat(label.style.left) - label.offsetWidth / 2.0) + 'px';
		label.style.top = (parseFloat(label.style.top) + label.offsetHeight / 2.0) + 'px';
	});
}
