sandbox$ = {

selectedPoints: {},
selectedSegments: {},
board: null,

options: {
	color: '#212121',
	hl_color: '#F44336',
},

initScene: function(l, t, r, b) {
	this.board = JXG.JSXGraph.initBoard('scene', {
		boundingbox: [l, t, r, b],
		keepaspectratio: true,
		showNavigation: false,
		showCopyright: false,
		registerEvents: false
	});
},

addPoint: function(name, x, y) {
	this.board.create('point', [x, y], {
		name: name,
		id: name,
		color: this.options.color,
		highlightFillColor: this.options.hl_color,
		highlightStrokeColor: this.options.hl_color,
		size: 3,
		label: {color: this.options.color, autoPosition: true}
	});
},

addLine: function(pt0, pt1) {
	this.board.create('line', [this.board.elementsByName[pt0], this.board.elementsByName[pt1]], {
		straightFirst: false,
		straightLast: false,
		strokeWidth: 0.7,
		color: this.options.color
	});
},

setupTree: function() {
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
				item.addEventListener('click', function() {
					if (item.classList.contains('selected')) {
						points.forEach(id => {
							var count = sandbox$.selectedPoints[id] - 1;
							if (count == 0) {
								sandbox$.board.elementsByName[id].noHighlight();
							}
							sandbox$.selectedPoints[id] = count;
						});
						sandbox$.selectedSegments[cls].forEach(obj => {sandbox$.board.removeObject(obj);});
						delete sandbox$.selectedSegments[cls];
						root.querySelectorAll('.' + cls).forEach(elt => {elt.classList.remove('selected');});
					} else {
						points.forEach(id => {
							sandbox$.selectedPoints[id] = (sandbox$.selectedPoints[id] || 0) + 1;
							sandbox$.board.elementsByName[id].highlight(); }
						);
						var selected = [];
						lines.forEach(ln => {
							selected.push(sandbox$.board.create(
								'line', [sandbox$.board.elementsByName[ln['s']], sandbox$.board.elementsByName[ln['e']]], {
									straightFirst: false,
									straightLast: ln['type'] == 'ray',
									color: sandbox$.options.hl_color,
									strokeWidth: 1.0
								})
							);
						});
						sandbox$.selectedSegments[cls] = selected;
						root.querySelectorAll('.' + cls).forEach(elt => {elt.classList.add('selected');});
					}
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
		item.querySelector('span.handler').addEventListener('click', function(e) {
			item.classList.toggle('open');
			item.classList.toggle('closed');
			e.stopPropagation();
		});
	});
},

toggleNonEssential: function() {
	var root = document.getElementById('gsb-tree');
	var props = root.querySelectorAll('.normal');
	if (root.querySelector('#checkbox').checked) {
		props.forEach(item => { item.style.display='none'; });
	} else {
		props.forEach(item => { item.style.display='block'; });
	}
	root.querySelectorAll('li').forEach(item => {
		var list = item.querySelector('ul');
		if (list == null) {
			return;
		}
		var hasVisibleChildren = false;
		for (var i = 0; i < list.children.length; i++) {
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
}

};
