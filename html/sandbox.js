sandbox$ = {

selectedPoints: {},
selectedSegments: {},
board: null,

options: {
	color: '#212121',
	hl_color: '#F44336',
},

initScene: function(l, t, r, b) {
	this.board = JXG.JSXGraph.initBoard('sandbox-scene', {
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
	var root = $('#sandbox-tree');
	root.find('span').each(function() {
		if ($(this).parent().prop('tagName').toLowerCase() == 'span') {
			return;
		}

		var clazz = null;
		var points = null;
		var lines = [];
		$(this)[0].classList.forEach(cls => {
			clazz = cls;
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
			} else if (cls.startsWith('ln__')) {
				points = cls.split('__').slice(1, 3);
				lines = [{s: points[0], e: points[1], type: 'line'}];
			} else if (cls.startsWith('seg__')) {
				points = cls.split('__').slice(1, 3);
				lines = [{s: points[0], e: points[1]}];
			} else if (cls.startsWith('pt__')) {
				points = cls.split('__').slice(1, 2);
			}
		});

		if (points) {
			$(this).click(function() {
				var deselect = function() {
					var tag = $('#sandbox-selections').find('.' + clazz);
					tag.next().remove();
					tag.remove();
					points.forEach(id => {
						var count = sandbox$.selectedPoints[id] - 1;
						if (count == 0) {
							sandbox$.board.elementsByName[id].noHighlight();
						}
						sandbox$.selectedPoints[id] = count;
					});
					sandbox$.selectedSegments[clazz].forEach(obj => {sandbox$.board.removeObject(obj);});
					delete sandbox$.selectedSegments[clazz];
					root.find('.' + clazz).each(function() { $(this).removeClass('selected'); });
				};
				if ($(this).hasClass('selected')) {
					deselect();
				} else {
					var clone = $(this).clone();
					clone.addClass('selected');
					clone.click(deselect);
					var area = $('#sandbox-selections');
					area.append(clone);
					area.append('<span class="space"></span>');
					points.forEach(id => {
						sandbox$.selectedPoints[id] = (sandbox$.selectedPoints[id] || 0) + 1;
						sandbox$.board.elementsByName[id].highlight(); }
					);
					var selected = [];
					lines.forEach(ln => {
						selected.push(sandbox$.board.create(
							'line', [sandbox$.board.elementsByName[ln['s']], sandbox$.board.elementsByName[ln['e']]], {
								straightFirst: ln['type'] == 'line',
								straightLast: ln['type'] == 'ray' || ln['type'] == 'line',
								color: sandbox$.options.hl_color,
								strokeWidth: 1.0
							})
						);
					});
					sandbox$.selectedSegments[clazz] = selected;
					root.find('.' + clazz).each(function() { $(this).addClass('selected'); });
					sandbox$.board.update();
					sandbox$.board.update();
				}
			});
		}
	});
	root.find('li').each(function() {
		var element = $(this);
		if (element.find('ul')) {
			element.addClass('closed');
			element.removeClass('open');
			element.find('span.handler').first().click(function() {
				element.toggleClass('open');
				element.toggleClass('closed');
			});
		}
	});
},

toggleNonEssential: function() {
	var root = $('#sandbox-tree');
	var hideNonEssential = root.find('#checkbox').is(':checked');
	root.find('.normal').each(function() {
		$(this).css('display', hideNonEssential ? 'none' : 'block');
	});
	root.find('li').each(function() {
		var list = $(this).find('ul').first();
		if (!list) {
			return;
		}
		var hasVisibleChildren = false;
		list.children().each(function() {
			if ($(this).css('display') != 'none') {
				hasVisibleChildren = true;
				return false;
			}
			return true;
		});
		if (hasVisibleChildren) {
			$(this).removeClass('empty');
		} else {
			$(this).addClass('empty');
		}
	});
},

updateLabels: function() {
	setTimeout(function() {
		console.debug('labels layout hack');
		sandbox$.board.update();
	}, 0);
}

};
