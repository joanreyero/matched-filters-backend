from flask import Flask, request, send_file
from flask_cors import CORS
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from werkzeug.datastructures import ImmutableMultiDict
from matchedFilters import MatchedFilter
import matplotlib.pyplot as plt
import io, base64, ast
import numpy as np

app = Flask(__name__)
CORS(app)

def make_mf(r):
    args = r.args.to_dict(flat=False)
    mf = MatchedFilter(int(args['x'][0]), int(args['y'][0]),
                       list(map(float, args['fov[]'])),
                       args['fovType'][0],
                       orientation=list(map(float, args['orientation[]'])),
                       axis=list(map(float, args['axis[]'])))
    return mf

@app.route('/plot', methods=['GET'])
def build_plot():
    mf = make_mf(request)
    fig = mf.plot()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return output.getvalue()


@app.route('/matched_filter', methods=['GET'])
def get_filter():
    mf = make_mf(request)
    output = io.StringIO()
    for sl in [0, 1]:
        sl_msg = f'\n\n Slice {sl}\n'
        output.write(sl_msg)
        np.savetxt(output, mf.matched_filter[:,:,sl])
        
    return output.getvalue()


# @app.route('/filt', methods=['GET'])
# def get_filter():
#     mf = make_mf(request)
#     output = io.BytesIO()
#     for sl in [0, 1]:
#         sl_msg = b'\n\n Slice {sl}\n'
#         output.write(sl_msg)
#         output.write(mf.matched_filter[:,:,sl].tobytes())

#     output.seek(0)
#     return send_file(output,
#                      as_attachment=True,
#                      attachment_filename='test.txt',
#                      mimetype='text/csv'
#     )


if __name__ == '__main__':
    app.debug = True
    app.run()
