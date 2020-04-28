sandbox$ = {

selectedPoints: {},
selectedSegments: {},
board: null,

options: {
	color: '#212121',
	hl_color: '#F44336',
},

createScene: function(json) {
	var scene = JSON.parse(json);
	var xs = [];
	var ys = [];
	scene.points.forEach(pt => {
		xs.push(pt.x);
		ys.push(pt.y);
	});
	var max_x = Math.max(... xs);
	var min_x = Math.min(... xs);
	var max_y = Math.max(... ys);
	var min_y = Math.min(... ys);
  var mid_x = (min_x + max_x) / 2;
  var mid_y = (min_y + max_y) / 2;
	var size = Math.max(max_x - min_x, max_y - min_y) * 1.3;
	this.board = JXG.JSXGraph.initBoard('sandbox-scene', {
		boundingbox: [mid_x - size / 2, mid_y - size / 2, mid_x + size / 2, mid_y + size / 2],
		keepaspectratio: true,
		showNavigation: false,
		showCopyright: false,
		registerEvents: false
	});

	scene.points.forEach(pt => {
		this.board.create('point', [pt.x, pt.y], {
			name: pt.name,
			id: pt.name,
			color: this.options.color,
			highlightFillColor: this.options.hl_color,
			highlightStrokeColor: this.options.hl_color,
			size: 3,
			label: {color: this.options.color, autoPosition: true}
		});
	});

	scene.lines.forEach(line => {
		this.board.create('line', [this.board.elementsByName[line.pt0], this.board.elementsByName[line.pt1]], {
			straightFirst: false,
			straightLast: false,
			strokeWidth: 0.7,
			color: this.options.color
		});
	});

	setTimeout(function() {
		console.debug('labels layout hack');
		sandbox$.board.update();
	}, 0);
},

createTree: function(json) {
	var root = $('#sandbox-tree');

	var data = JSON.parse(json);
	var buildTree = function(root, index) {
		var obj = data[index];
		var item = $('<li/>');
		item.addClass(obj.priority);
		item.append('<span class="handler"/>');
		item.append(obj.property);
		item.append('<span class="implication">⇐</span>');
		item.append(obj.comment);
		if (obj.premises.length > 0) {
			var list = $('<ul/>');
			obj.premises.forEach(ind => { buildTree(list, ind); });
			item.append(list);
		}
		root.append(item);
	};
	var tree = $('<ul/>');
	buildTree(tree, 0);
	root.append(tree);

	root.find('span').each(function() {
		if ($(this).parent('.figure').length > 0) {
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
					$('#sandbox-selections').find('.' + clazz).each(function() {
						if ($(this).parent('.figure').length == 0) {
							$(this).next().remove();
							$(this).remove();
						}
					});
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
					area.append('<span class="space"/>');
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
			element.find('span.handler').first().click(function(e) {
				if (e.shiftKey) {
					if (element.hasClass('closed')) {
						element.find('.closed').removeClass('closed').addClass('open');
					} else if (element.hasClass('open')) {
						element.find('.open').removeClass('open').addClass('closed');
					}
				}
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
		var hide = !$(this).find('.essential').exists && hideNonEssential;
		$(this).css('display', hide ? 'none' : 'block');
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
}

};
