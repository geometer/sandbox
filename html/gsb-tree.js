function setupTree() {
	root = document.getElementById('gsb-tree');
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
						selectedSegments.push(board.create("line", [idToPoint[ln['s']], idToPoint[ln['e']]], {straightFirst:false, straightLast:ln['type'] == 'ray', color:"#00E6E3", strokeWidth:1.5}));
					});
					root.querySelectorAll('.' + cls).forEach(elt => {elt.style.background = "#00E6E3";});
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
